from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class TuvCertificate(models.Model):
    """The certificate of an audit, from its preparation onwards.

    It can only come into existence once the audit report is approved, every Major
    NC is closed and the invoices are 100% paid - checked on creation itself, so no
    button, import or server code can start one early.
    """

    _name = 'tuv.certificate'
    _description = 'Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Certificate', compute='_compute_name', store=True)
    project_id = fields.Many2one('project.project', string='Audit Project', required=True,
                                 readonly=True, ondelete='restrict', index=True)
    partner_id = fields.Many2one(related='project_id.partner_id', string='Certificate Holder', store=True)
    state = fields.Selection([
        ('preparation', 'In Preparation'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='preparation', required=True, tracking=True)
    initiated_on = fields.Datetime(string='Preparation Started', default=fields.Datetime.now, readonly=True)
    initiated_by = fields.Many2one('res.users', string='Started By', default=lambda s: s.env.user, readonly=True)
    trigger = fields.Char(string='Started By Event', readonly=True)

    # What the certificate will state, taken from the audit when preparation starts and
    # editable while it is prepared
    standards = fields.Char(string='Standard(s)')
    ea_code_ids = fields.Many2many('industry.ea.code', 'tuv_certificate_ea_code_rel',
                                   'certificate_id', 'ea_code_id', string='EA Code')
    scope = fields.Text(string='Certified Scope')
    site_address = fields.Text(string='Certified Site(s)')
    lead_auditor_id = fields.Many2one('res.partner', string='Lead Auditor')
    audit_date_st1 = fields.Date(string='Audit Date St.1')
    audit_date_st2 = fields.Date(string='Audit Date St.2')

    # The three conditions it was started on, for the record
    technical_review_id = fields.Many2one('tuv.technical.review', string='Approved Technical Review', readonly=True)
    report_conclusion = fields.Selection(related='project_id.report_conclusion', string='Audit Conclusion')
    major_nc_closed = fields.Integer(string='Major NCs Closed', readonly=True)
    minor_nc_open = fields.Integer(string='Minor NCs Still Open', readonly=True)
    amount_paid = fields.Monetary(string='Amount Paid', readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', readonly=True)
    notes = fields.Text(string='Preparation Notes')

    _one_active_per_project = models.UniqueIndex(
        "(project_id) WHERE (state != 'cancelled')",
        'This project already has a certificate in progress.',
    )

    @api.depends('partner_id', 'standards', 'project_id')
    def _compute_name(self):
        for cert in self:
            cert.name = '%s - %s' % (cert.partner_id.name or '', cert.standards or cert.project_id.name or '')

    @api.model_create_multi
    def create(self, vals_list):
        # the control itself: holds for every caller, sudo included
        for vals in vals_list:
            project = self.env['project.project'].browse(vals.get('project_id'))
            if project.certificate_id:
                raise ValidationError(_('%(project)s already has a certificate in progress: %(cert)s.',
                                        project=project.name, cert=project.certificate_id.name))
            blockers = project._certificate_blockers() if project else [_('no project')]
            if blockers:
                raise ValidationError(_('The certificate of %(project)s cannot be initiated: %(why)s.',
                                        project=project.name, why='; '.join(blockers)))
        return super().create(vals_list)

    def action_cancel(self):
        if not self.env.user.has_group('base.group_system'):
            raise UserError(_('Only an administrator can cancel a certificate.'))
        self.write({'state': 'cancelled'})
        return True


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _reconcile_plan(self, reconciliation_plan):
        # every reconciliation passes here: the payment wizard, the bank reconciliation,
        # a manual match. A project that just became 100% paid starts its certificate.
        res = super()._reconcile_plan(reconciliation_plan)
        lines = self.browse()
        stack = list(reconciliation_plan)
        while stack:
            item = stack.pop()
            if isinstance(item, models.BaseModel):
                lines |= item
            elif isinstance(item, (list, tuple)):
                stack.extend(item)
        projects = lines.move_id.tuv_project_id
        if projects:
            projects._trigger_certificate_preparation(_('full payment received'), announce_waiting=True)
        return res


class ProjectProject(models.Model):
    _inherit = 'project.project'

    certificate_ids = fields.One2many('tuv.certificate', 'project_id', string='Certificates')
    certificate_id = fields.Many2one('tuv.certificate', compute='_compute_certificate_id', string='Certificate')
    certificate_state = fields.Selection(
        lambda self: self.env['tuv.certificate']._fields['state'].selection,
        compute='_compute_certificate_id', string='Certificate Progress')

    @api.depends('certificate_ids.state')
    def _compute_certificate_id(self):
        for project in self:
            project.certificate_id = project.certificate_ids.filtered(lambda c: c.state != 'cancelled')[:1]
            project.certificate_state = project.certificate_id.state

    # ------------------------------------------------------------------
    # The three conditions
    # ------------------------------------------------------------------
    def _certificate_blockers(self):
        self.ensure_one()
        blockers = []
        if self.technical_review_state != 'approved':
            blockers.append(_('the audit report is not approved by technical review'))
        open_major = self.nonconformity_ids.filtered(
            lambda n: n.grade == 'major_nc' and n.state in ('open', 'submitted'))
        if open_major:
            blockers.append(_('%(count)s Major NC(s) still open (%(names)s)',
                              count=len(open_major), names=', '.join(open_major.mapped('name'))))
        return blockers + super()._certificate_blockers()

    @api.depends('technical_review_state', 'nonconformity_ids.state', 'nonconformity_ids.grade')
    def _compute_certificate_blocked_reason(self):
        return super()._compute_certificate_blocked_reason()

    # ------------------------------------------------------------------
    # Start the preparation the moment the last condition is met
    # ------------------------------------------------------------------
    def _trigger_certificate_preparation(self, trigger, announce_waiting=False):
        Certificate = self.env['tuv.certificate'].sudo()
        planning = self.env.ref('tuv_austria_customization.group_planning_team', raise_if_not_found=False)
        planners = self.env['res.users'].search([('all_group_ids', 'in', planning.id)]) if planning else self.env['res.users']
        for project in self.sudo():
            if project.audit_state != 'done' or project.certificate_id:
                continue
            blockers = project._certificate_blockers()
            if blockers:
                if announce_waiting and project.payment_status == 'paid':
                    project.message_post(body=_('Full payment received - certificate preparation is waiting '
                                                'for: %s.', '; '.join(blockers)))
                continue
            review = project.technical_review_ids.filtered(lambda r: r.state == 'approved').sorted('id')[-1:]
            ncs = project.nonconformity_ids
            cert = Certificate.create({
                'project_id': project.id,
                'trigger': trigger,
                'standards': project.atjf_standards,
                'ea_code_ids': [(6, 0, project.ea_code_ids.ids)],
                'scope': project.audit_scope,
                'site_address': project.atjf_site_address,
                'lead_auditor_id': project.auditor_id.id,
                'audit_date_st1': project.md_audit_date_st1,
                'audit_date_st2': project.md_audit_date_st2,
                'technical_review_id': review.id,
                'major_nc_closed': len(ncs.filtered(lambda n: n.grade == 'major_nc' and n.state == 'closed')),
                'minor_nc_open': len(ncs.filtered(lambda n: n.grade == 'minor_nc' and n.state in ('open', 'submitted'))),
                'amount_paid': project.amount_paid,
                'currency_id': project.payment_currency_id.id,
            })
            for user in planners or self.env.user:
                cert.activity_schedule('mail.mail_activity_data_todo', user_id=user.id,
                                       summary=_('Prepare the certificate - %s', cert.name))
            # the client's own flow: the project enters Certificate Issuance
            stage = self.env['project.project.stage'].search([], order='sequence, id').filtered(
                lambda s: s._is_certificate_stage())[:1]
            if stage and (not project.stage_id or project.stage_id.sequence < stage.sequence):
                project.stage_id = stage
            body = _('Certificate preparation started automatically (%(trigger)s): report approved, all Major '
                     'NCs closed, 100%% paid.', trigger=trigger)
            project.message_post(body=body)
            cert.message_post(body=body)

    def action_initiate_certificate(self):
        """Button: start it by hand - refused with the reasons unless all three hold."""
        self.ensure_one()
        blockers = self._certificate_blockers()
        if blockers:
            raise UserError(_('The certificate cannot be initiated: %s.', '; '.join(blockers)))
        self._trigger_certificate_preparation(_('started by %s', self.env.user.name))
        return self.action_view_certificate()

    def action_view_certificate(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'res_model': 'tuv.certificate', 'name': _('Certificate'),
            'view_mode': 'form', 'res_id': self.certificate_id.id, 'target': 'current',
        }

    @api.model
    def _cron_payment_tracking(self):
        res = super()._cron_payment_tracking()
        # safety net: anything fully paid and otherwise ready starts here at the latest
        self.search([('payment_status', '=', 'paid'), ('audit_state', '=', 'done')])._trigger_certificate_preparation(
            _('hourly check'))
        return res


class TechnicalReview(models.Model):
    _inherit = 'tuv.technical.review'

    def action_approve(self):
        res = super().action_approve()
        self.project_id._trigger_certificate_preparation(_('audit report approved'))
        return res


class AuditNonconformity(models.Model):
    _inherit = 'tuv.audit.nonconformity'

    def action_confirm_closure(self):
        res = super().action_confirm_closure()
        self.project_id._trigger_certificate_preparation(_('last Major NC closed'))
        return res
