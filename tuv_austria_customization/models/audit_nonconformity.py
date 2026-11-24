from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .search_utils import boolean_search_positive

# Months the client has to close a nonconformity, counted from the audit completion.
CLOSURE_MONTHS = {'major_nc': 3, 'minor_nc': 6}
NC_GRADE = [('major_nc', 'Major'), ('minor_nc', 'Minor')]


class AuditNonconformity(models.Model):
    """A nonconformity raised at the audit, followed until its closure is confirmed."""

    _name = 'tuv.audit.nonconformity'
    _description = 'Audit Nonconformity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'deadline, id'

    name = fields.Char(string='NC Number', required=True, copy=False, readonly=True, default='/')
    project_id = fields.Many2one('project.project', string='Project', required=True,
                                 ondelete='cascade', index=True)
    partner_id = fields.Many2one(related='project_id.partner_id', string='Client', store=True)
    checklist_line_id = fields.Many2one('tuv.audit.checklist.line', string='Checklist Clause',
                                        ondelete='set null', index=True)
    standard = fields.Selection(related='checklist_line_id.standard', store=True)
    clause = fields.Char(string='Clause')
    requirement = fields.Char(string='Requirement')
    grade = fields.Selection(NC_GRADE, string='Grade', required=True, tracking=True)
    description = fields.Text(string='Nonconformity / Objective Evidence', required=True)
    auditor_id = fields.Many2one('res.partner', string='Raised By')

    raised_on = fields.Date(string='Raised On', required=True, default=fields.Date.context_today)
    deadline = fields.Date(string='Closure Deadline', compute='_compute_deadline', store=True,
                           tracking=True, help='Major: 3 months, Minor: 6 months after the audit.')
    days_left = fields.Integer(string='Days Left', compute='_compute_overdue')
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_overdue', search='_search_overdue')
    overdue_notified = fields.Boolean(copy=False)

    state = fields.Selection([
        ('open', 'Open'),
        ('submitted', 'Corrective Action Received'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='open', required=True, tracking=True, copy=False)

    # What the client sends back
    root_cause = fields.Text(string='Root Cause')
    correction = fields.Text(string='Correction')
    corrective_action = fields.Text(string='Corrective Action')
    client_evidence = fields.Binary(string='Client Evidence', attachment=True)
    client_evidence_name = fields.Char(string='Client Evidence File')
    submitted_on = fields.Date(string='Received On', readonly=True, copy=False)

    # The confirmation that closes it
    closure_note = fields.Text(string='Closure Verification')
    closed_on = fields.Date(string='Closed On', readonly=True, copy=False)
    closed_by = fields.Many2one('res.users', string='Closure Confirmed By', readonly=True, copy=False)
    closed_on_time = fields.Boolean(string='Closed On Time', readonly=True, copy=False)
    reject_reason = fields.Text(string='Last Rejection Reason', readonly=True, copy=False)

    @api.depends('grade', 'raised_on')
    def _compute_deadline(self):
        for nc in self:
            months = CLOSURE_MONTHS.get(nc.grade)
            nc.deadline = nc.raised_on + relativedelta(months=months) if months and nc.raised_on else False

    @api.depends('deadline', 'state')
    def _compute_overdue(self):
        today = fields.Date.context_today(self)
        for nc in self:
            nc.days_left = (nc.deadline - today).days if nc.deadline else 0
            nc.is_overdue = nc.state in ('open', 'submitted') and bool(nc.deadline) and nc.deadline < today

    def _search_overdue(self, operator, value):
        today = fields.Date.context_today(self)
        domain = [('state', 'in', ('open', 'submitted')), ('deadline', '<', today)]
        return domain if boolean_search_positive(operator, value) else ['!', '&'] + domain

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('tuv.audit.nonconformity') or '/'
        records = super().create(vals_list)
        for nc in records:
            nc.activity_schedule(
                'mail.mail_activity_data_todo', date_deadline=nc.deadline,
                user_id=(nc.project_id.user_id or self.env.user).id,
                summary=_('%(grade)s NC %(name)s - close by %(deadline)s', grade=nc._grade_label(),
                          name=nc.name, deadline=nc.deadline))
        return records

    def _grade_label(self):
        return dict(NC_GRADE)[self.grade]

    # ------------------------------------------------------------------
    # Open -> Corrective Action Received -> Closed
    # ------------------------------------------------------------------
    def action_submit_corrective_action(self):
        for nc in self:
            if nc.state != 'open':
                raise UserError(_('%s is not open.', nc.name))
            missing = [label for value, label in (
                (nc.root_cause, _('Root Cause')),
                (nc.corrective_action, _('Corrective Action')),
                (nc.client_evidence, _('Client Evidence')),
            ) if not value]
            if missing:
                raise UserError(_('%(name)s: fill in what the client sent before recording it:\n- %(list)s',
                                  name=nc.name, list='\n- '.join(missing)))
            nc.write({'state': 'submitted', 'submitted_on': fields.Date.context_today(nc)})
            nc.message_post(body=_('Corrective action received from the client.'))
        return True

    def action_confirm_closure(self):
        user = self.env.user
        if not (user.has_group('tuv_austria_customization.group_planning_team')
                or user.has_group('base.group_system')):
            raise UserError(_('Only the planning team can confirm the closure of a nonconformity.'))
        for nc in self:
            if nc.state != 'submitted':
                raise UserError(_('%s: record the client\'s corrective action first.', nc.name))
            if not nc.closure_note:
                raise UserError(_('%s: write how the closure was verified.', nc.name))
            today = fields.Date.context_today(nc)
            nc.write({
                'state': 'closed', 'closed_on': today, 'closed_by': user.id,
                'closed_on_time': bool(nc.deadline) and today <= nc.deadline,
            })
            nc.activity_feedback(['mail.mail_activity_data_todo'], feedback=_('Closure confirmed.'))
            nc.message_post(body=_('Closure confirmed by %(user)s %(timing)s.', user=user.name,
                                   timing=_('within the deadline') if nc.closed_on_time
                                   else _('after the deadline')))
            nc.project_id.message_post(body=_('%(grade)s NC %(name)s (clause %(clause)s) closed.',
                                              grade=nc._grade_label(), name=nc.name, clause=nc.clause))
        return True

    def action_reject_corrective_action(self):
        """The evidence does not close it: back to the client."""
        for nc in self:
            if nc.state != 'submitted':
                raise UserError(_('%s has no corrective action to reject.', nc.name))
            if not nc.closure_note:
                raise UserError(_('%s: write in "Closure Verification" why it is not accepted.', nc.name))
            nc.write({'state': 'open', 'reject_reason': nc.closure_note, 'closure_note': False,
                      'submitted_on': False})
            nc.message_post(body=_('Corrective action not accepted: %s', nc.reject_reason))
        return True

    # ------------------------------------------------------------------
    # Daily: tell the planning team about the ones past their deadline
    # ------------------------------------------------------------------
    @api.model
    def _cron_flag_overdue(self):
        overdue = self.search([('is_overdue', '=', True), ('overdue_notified', '=', False)])
        for nc in overdue:
            nc.message_post(body=_('Overdue: the closure deadline %s has passed.', nc.deadline))
            nc.activity_schedule(
                'mail.mail_activity_data_todo', user_id=(nc.project_id.user_id or self.env.user).id,
                summary=_('OVERDUE %(grade)s NC %(name)s - deadline %(deadline)s',
                          grade=nc._grade_label(), name=nc.name, deadline=nc.deadline))
        overdue.write({'overdue_notified': True})
        return len(overdue)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    nonconformity_ids = fields.One2many('tuv.audit.nonconformity', 'project_id', string='Nonconformities')
    nc_open_count = fields.Integer(compute='_compute_nc_counts', string='Open NCs')
    nc_closed_count = fields.Integer(compute='_compute_nc_counts', string='Closed NCs')
    nc_overdue_count = fields.Integer(compute='_compute_nc_counts', string='Overdue NCs')

    @api.depends('nonconformity_ids.state', 'nonconformity_ids.deadline')
    def _compute_nc_counts(self):
        for project in self:
            ncs = project.nonconformity_ids
            project.nc_open_count = len(ncs.filtered(lambda n: n.state in ('open', 'submitted')))
            project.nc_closed_count = len(ncs.filtered(lambda n: n.state == 'closed'))
            project.nc_overdue_count = len(ncs.filtered('is_overdue'))

    def _sync_nonconformities(self):
        """Log one nonconformity per Major / Minor checklist clause of the audit."""
        NC = self.env['tuv.audit.nonconformity']
        for project in self:
            raised_on = (project.audit_completed_on or fields.Datetime.now()).date()
            for line in project.audit_line_ids:
                nc = project.nonconformity_ids.filtered(
                    lambda n: n.checklist_line_id == line and n.state != 'cancelled')[:1]
                if line.result in CLOSURE_MONTHS:
                    if not nc:
                        NC.create({
                            'project_id': project.id, 'checklist_line_id': line.id,
                            'clause': line.code, 'requirement': line.name, 'grade': line.result,
                            'description': line.evidence or line.name,
                            'auditor_id': line.auditor_id.id, 'raised_on': raised_on,
                        })
                    elif nc.state == 'open' and nc.grade != line.result:
                        nc.grade = line.result   # regraded after a reopened audit
                elif nc and nc.state == 'open':
                    nc.state = 'cancelled'       # the clause is no longer a nonconformity
                    nc.activity_unlink(['mail.mail_activity_data_todo'])

    def action_audit_complete(self):
        res = super().action_audit_complete()
        self._sync_nonconformities()
        for project in self:
            if project.nc_open_count:
                project.message_post(body=_('%s nonconformity(ies) logged with their closure deadlines.',
                                            project.nc_open_count))
        return res

    def action_view_nonconformities(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'tuv_austria_customization.action_tuv_audit_nonconformity')
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id': self.id}
        return action
