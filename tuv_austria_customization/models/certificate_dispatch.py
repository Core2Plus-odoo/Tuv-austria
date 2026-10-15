import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError

DISPATCH_METHODS = [
    ('courier', 'Courier'),
    ('email', 'Email'),
    ('in_person', 'In Person'),
]
# What the approver confirms before the certificate may be printed
CERT_CHECKS = [
    ('chk_holder', 'Client name and address are correct'),
    ('chk_standard_scope', 'Standard and certified scope match the audit and the approved report'),
    ('chk_ea', 'EA code matches the certified scope'),
    ('chk_dates', 'Certificate number, issue date, expiry and surveillance dates are correct'),
]


class TuvCertificate(models.Model):
    _inherit = 'tuv.certificate'

    state = fields.Selection(
        selection_add=[('approved', 'Approved'), ('printed', 'Printed'), ('dispatched', 'Dispatched'),
                       ('cancelled',)],
        ondelete={'approved': 'set default', 'printed': 'set default', 'dispatched': 'set default'})

    chk_holder = fields.Boolean(string=CERT_CHECKS[0][1])
    chk_standard_scope = fields.Boolean(string=CERT_CHECKS[1][1])
    chk_ea = fields.Boolean(string=CERT_CHECKS[2][1])
    chk_dates = fields.Boolean(string=CERT_CHECKS[3][1])
    review_comments = fields.Text(string='Review Comments')
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False)
    approved_on = fields.Datetime(string='Approved On', readonly=True, copy=False)

    printed_by = fields.Many2one('res.users', string='Printed By', readonly=True, copy=False)
    printed_on = fields.Datetime(string='Printed On', readonly=True, copy=False)
    print_count = fields.Integer(string='Times Printed', readonly=True, copy=False)
    final_pdf_id = fields.Many2one('ir.attachment', string='Printed Certificate', readonly=True, copy=False)

    dispatch_ids = fields.One2many('tuv.certificate.dispatch', 'certificate_id', string='Dispatch Log')
    dispatched_on = fields.Date(string='First Dispatched On', readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Review & approval
    # ------------------------------------------------------------------
    def _check_approver(self):
        user = self.env.user
        if not (user.has_group('tuv_austria_customization.group_certificate_approver')
                or user.has_group('base.group_system')):
            raise UserError(_('Only a Certificate Approver can review and approve a certificate.'))

    def action_approve_certificate(self):
        self._check_approver()
        for cert in self:
            if cert.state != 'prepared':
                raise UserError(_('Only a prepared certificate can be approved.'))
            if cert.prepared_by == self.env.user:
                raise UserError(_('%s prepared this certificate: it has to be approved by someone else.',
                                  self.env.user.name))
            unticked = [label for field, label in CERT_CHECKS if not cert[field]]
            if unticked:
                raise UserError(_('Confirm every point of the review first:\n- %s', '\n- '.join(unticked)))
            blockers = cert.project_id._certificate_blockers()
            if blockers:
                raise UserError(_('The certificate cannot be approved: %s.', '; '.join(blockers)))
            cert.write({'state': 'approved', 'approved_by': self.env.user.id,
                        'approved_on': fields.Datetime.now()})
            cert._log(_('Certificate %(number)s reviewed and approved by %(user)s.',
                        number=cert.certificate_number, user=self.env.user.name))
        return True

    def action_return_to_preparation(self):
        self._check_approver()
        for cert in self:
            if cert.state != 'prepared':
                raise UserError(_('Only a prepared certificate can be returned.'))
            if not cert.review_comments:
                raise UserError(_('Write in the review comments what has to be corrected.'))
            # the number stays with the certificate; confirming again keeps it
            cert.write({'state': 'preparation'})
            cert._log(_('Certificate returned to preparation by %(user)s: %(why)s',
                        user=self.env.user.name, why=cert.review_comments))
        return True

    # ------------------------------------------------------------------
    # Print
    # ------------------------------------------------------------------
    def action_print_certificate(self):
        self.ensure_one()
        if self.state not in ('approved', 'printed', 'dispatched'):
            raise UserError(_('The certificate can only be printed once it is approved.'))
        report = self.env.ref('tuv_austria_customization.action_report_tuv_certificate')
        pdf, _type = report._render_qweb_pdf(report.report_name, self.ids)
        filename = 'Certificate %s.pdf' % (self.certificate_number or '').replace('/', '-')
        attachment = self.env['ir.attachment'].create({
            'name': filename, 'datas': base64.b64encode(pdf), 'mimetype': 'application/pdf',
            'res_model': self._name, 'res_id': self.id,
        })
        vals = {'printed_by': self.env.user.id, 'printed_on': fields.Datetime.now(),
                'print_count': self.print_count + 1, 'final_pdf_id': attachment.id}
        if self.state == 'approved':
            vals['state'] = 'printed'
        self.write(vals)
        self._log(_('Certificate %(number)s printed by %(user)s (print %(count)s).',
                    number=self.certificate_number, user=self.env.user.name, count=self.print_count))
        return {'type': 'ir.actions.act_url', 'target': 'new',
                'url': '/web/content/%s?download=true' % attachment.id}

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    def action_open_dispatch(self):
        self.ensure_one()
        if self.state not in ('printed', 'dispatched'):
            raise UserError(_('Print the approved certificate before dispatching it.'))
        return {
            'type': 'ir.actions.act_window', 'name': _('Log Dispatch'),
            'res_model': 'tuv.certificate.dispatch.wizard', 'view_mode': 'form', 'target': 'new',
            'context': {'default_certificate_id': self.id},
        }

    def _log(self, body):
        for cert in self:
            cert.message_post(body=body)
            cert.project_id.sudo().message_post(body=body)


class TuvCertificateDispatch(models.Model):
    """One delivery of a certificate to the client."""

    _name = 'tuv.certificate.dispatch'
    _description = 'Certificate Dispatch'
    _order = 'dispatch_date desc, id desc'

    certificate_id = fields.Many2one('tuv.certificate', required=True, ondelete='cascade', index=True)
    certificate_number = fields.Char(related='certificate_id.certificate_number', store=True)
    partner_id = fields.Many2one(related='certificate_id.partner_id', store=True, string='Client')
    dispatch_date = fields.Date(string='Dispatch Date', required=True)
    method = fields.Selection(DISPATCH_METHODS, string='Method of Delivery', required=True)
    courier_name = fields.Char(string='Courier Company')
    tracking_number = fields.Char(string='Tracking Number')
    recipient_name = fields.Char(string='Received By')
    email_to = fields.Char(string='Sent To')
    note = fields.Char(string='Note')
    logged_by = fields.Many2one('res.users', string='Logged By', default=lambda s: s.env.user, readonly=True)


class TuvCertificateDispatchWizard(models.TransientModel):
    _name = 'tuv.certificate.dispatch.wizard'
    _description = 'Log Certificate Dispatch'

    certificate_id = fields.Many2one('tuv.certificate', required=True)
    partner_id = fields.Many2one(related='certificate_id.partner_id')
    dispatch_date = fields.Date(string='Dispatch Date', required=True, default=fields.Date.context_today)
    method = fields.Selection(DISPATCH_METHODS, string='Method of Delivery', required=True, default='courier')
    courier_name = fields.Char(string='Courier Company')
    tracking_number = fields.Char(string='Tracking Number')
    recipient_name = fields.Char(string='Received By')
    # the client's own address: the certificate goes to the certificate holder
    email_to = fields.Char(string='Send To', compute='_compute_email_to')
    note = fields.Char(string='Note')

    @api.depends('certificate_id')
    def _compute_email_to(self):
        for wizard in self:
            wizard.email_to = wizard.certificate_id.partner_id.email

    def action_confirm(self):
        self.ensure_one()
        cert = self.certificate_id
        if cert.state not in ('printed', 'dispatched'):
            raise UserError(_('Print the approved certificate before dispatching it.'))
        required = {
            'courier': [(self.courier_name, _('Courier Company')), (self.tracking_number, _('Tracking Number'))],
            'in_person': [(self.recipient_name, _('Received By'))],
            'email': [(self.email_to, _('client e-mail address (on the contact)'))],
        }[self.method]
        missing = [label for value, label in required if not value]
        if missing:
            raise UserError(_('Fill in for this method of delivery: %s.', ', '.join(missing)))
        if self.method == 'email':
            template = self.env.ref('tuv_austria_customization.mail_template_certificate_dispatch')
            cert.message_post_with_source(template, partner_ids=cert.partner_id.ids,
                                          subtype_xmlid='mail.mt_comment', message_type='comment')
        self.env['tuv.certificate.dispatch'].create({
            'certificate_id': cert.id, 'dispatch_date': self.dispatch_date, 'method': self.method,
            'courier_name': self.courier_name if self.method == 'courier' else False,
            'tracking_number': self.tracking_number if self.method == 'courier' else False,
            'recipient_name': self.recipient_name if self.method == 'in_person' else False,
            'email_to': self.email_to if self.method == 'email' else False,
            'note': self.note,
        })
        method = dict(DISPATCH_METHODS)[self.method]
        detail = {
            'courier': _(' via %(courier)s, tracking %(tracking)s', courier=self.courier_name,
                         tracking=self.tracking_number),
            'in_person': _(', received by %s', self.recipient_name),
            'email': _(' to %s', self.email_to),
        }[self.method]
        cert._log(_('Certificate %(number)s dispatched on %(date)s by %(method)s%(detail)s.',
                    number=cert.certificate_number, date=self.dispatch_date, method=method, detail=detail))
        if cert.state == 'printed':
            cert.write({'state': 'dispatched', 'dispatched_on': self.dispatch_date})
            cert.activity_feedback(['mail.mail_activity_data_todo'], feedback=_('Certificate dispatched.'))
            # the client's flow moves on to its last stage
            project = cert.project_id.sudo()
            stage = self.env['project.project.stage'].search(
                [('name', '=', 'Feedback & Continuous Improvement')], limit=1)
            if stage and project.stage_id.sequence < stage.sequence:
                project.stage_id = stage
        return True
