from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# A certificate is suspended once its surveillance is this many months overdue.
SUSPENSION_OVERDUE_MONTHS = 3


def _check_notice_rights(env):
    user = env.user
    if not (user.has_group('tuv_austria_customization.group_planning_team')
            or user.has_group('tuv_austria_customization.group_certification_manager')
            or user.has_group('base.group_system')):
        raise UserError(_('Only the planning team or the Certification Manager can do this.'))


class ResCompany(models.Model):
    _inherit = 'res.company'

    withdrawal_grace_days = fields.Integer(
        string='Grace Period Before Withdrawal (days)', default=30,
        help='After a suspension notice the client has this many days to respond before the '
             'certificate is withdrawn.')


class TuvCertificate(models.Model):
    _inherit = 'tuv.certificate'

    certification_status = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('withdrawn', 'Withdrawn'),
    ], string='Certification Status', default='active', required=True, tracking=True, copy=False)
    notice_ids = fields.One2many('tuv.certificate.notice', 'certificate_id', string='Suspension / Withdrawal')


class CertificateNotice(models.Model):
    """A suspension or withdrawal notice, generated when the audit was not held in time."""

    _name = 'tuv.certificate.notice'
    _description = 'Suspension / Withdrawal Notice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'notice_date desc, id desc'

    name = fields.Char(string='Notice No.', required=True, readonly=True, copy=False, default='/')
    notice_type = fields.Selection([('suspension', 'Suspension'), ('withdrawal', 'Withdrawal')],
                                   string='Type', required=True, readonly=True)
    certificate_id = fields.Many2one('tuv.certificate', string='Certificate', required=True, readonly=True,
                                     ondelete='restrict', index=True)
    register_id = fields.Many2one('tuv.certificate.register', string='Register Entry', readonly=True)
    certificate_number = fields.Char(string='Certificate No.', readonly=True, index=True)
    partner_id = fields.Many2one('res.partner', string='Client', required=True, readonly=True)
    standards = fields.Char(string='Standard(s)', readonly=True)
    missed_due_date = fields.Date(string='Surveillance Was Due', readonly=True)
    notice_date = fields.Date(string='Notice Date', required=True, readonly=True)
    grace_end = fields.Date(string='Respond By', readonly=True,
                            help='No response by this date: the certificate is withdrawn.')
    suspension_id = fields.Many2one('tuv.certificate.notice', string='Suspension Notice', readonly=True)
    state = fields.Selection([
        ('awaiting', 'Awaiting Client Response'),
        ('responded', 'Client Responded'),
        ('lifted', 'Suspension Lifted'),
        ('escalated', 'Escalated To Withdrawal'),
        ('issued', 'Withdrawal Issued'),
    ], string='Status', required=True, readonly=True, tracking=True)
    response_note = fields.Text(string='Client Response')
    planned_audit_date = fields.Date(string='Agreed Audit Date')
    response_date = fields.Date(string='Responded On', readonly=True)
    lift_note = fields.Text(string='Reason For Lifting')
    lifted_on = fields.Date(string='Lifted On', readonly=True)
    lifted_by = fields.Many2one('res.users', string='Lifted By', readonly=True)
    sent_to = fields.Char(string='Sent To', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                code = 'tuv.notice.suspension' if vals.get('notice_type') == 'suspension' else 'tuv.notice.withdrawal'
                vals['name'] = self.env['ir.sequence'].next_by_code(code) or '/'
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Notify and log
    # ------------------------------------------------------------------
    def _issue(self):
        template_xmlid = {'suspension': 'mail_template_certificate_suspension',
                          'withdrawal': 'mail_template_certificate_withdrawal'}
        planning = self.env.ref('tuv_austria_customization.group_planning_team')
        managers = self.env.ref('tuv_austria_customization.group_certification_manager')
        staff = self.env['res.users'].search([('all_group_ids', 'in', (planning | managers).ids)])
        for notice in self:
            client = notice.partner_id
            if client.email:
                template = self.env.ref('tuv_austria_customization.' + template_xmlid[notice.notice_type])
                notice.message_post_with_source(template, partner_ids=client.ids,
                                                subtype_xmlid='mail.mt_comment', message_type='comment')
                notice.sent_to = client.email
            label = dict(self._fields['notice_type'].selection)[notice.notice_type]
            body = _('%(type)s notice %(name)s issued for certificate %(number)s (%(std)s)%(sent)s.',
                     type=label, name=notice.name, number=notice.certificate_number, std=notice.standards,
                     sent=_(' and sent to %s', client.email) if client.email else _(' - NOT e-mailed, the client has no e-mail'))
            cert = notice.certificate_id
            cert.message_post(body=body)
            if cert.project_id:
                cert.project_id.message_post(body=body)
            for user in staff or self.env.user:
                notice.activity_schedule(
                    'mail.mail_activity_data_todo', user_id=user.id,
                    date_deadline=notice.grace_end or notice.notice_date,
                    summary=_('%(type)s %(name)s - %(client)s', type=label, name=notice.name, client=client.name))

    # ------------------------------------------------------------------
    # The daily check
    # ------------------------------------------------------------------
    @api.model
    def _suspend(self, entry, today):
        cert = entry.certificate_id
        grace = self.env.company.withdrawal_grace_days or 30
        notice = self.create({
            'notice_type': 'suspension', 'certificate_id': cert.id, 'register_id': entry.id,
            'certificate_number': entry.name, 'partner_id': entry.partner_id.id, 'standards': entry.standards,
            'missed_due_date': entry.next_surveillance_date, 'notice_date': today,
            'grace_end': today + timedelta(days=grace), 'state': 'awaiting',
        })
        cert.certification_status = 'suspended'
        notice._issue()
        return notice

    @api.model
    def _withdraw(self, suspension, today):
        notice = self.create({
            'notice_type': 'withdrawal', 'certificate_id': suspension.certificate_id.id,
            'register_id': suspension.register_id.id, 'certificate_number': suspension.certificate_number,
            'partner_id': suspension.partner_id.id, 'standards': suspension.standards,
            'missed_due_date': suspension.missed_due_date, 'notice_date': today,
            'suspension_id': suspension.id, 'state': 'issued',
        })
        suspension.state = 'escalated'
        suspension.activity_unlink(['mail.mail_activity_data_todo'])
        suspension.certificate_id.certification_status = 'withdrawn'
        notice._issue()
        return notice

    @api.model
    def _cron_check(self, today=None):
        """Daily: suspend what is 3 months overdue, withdraw what did not respond in time."""
        today = today or fields.Date.context_today(self)
        Register = self.env['tuv.certificate.register']
        suspended = self.browse()
        for entry in Register.search([('is_current', '=', True), ('status', '=', 'valid')]):
            due = entry.next_surveillance_date
            if due and today > due + relativedelta(months=SUSPENSION_OVERDUE_MONTHS):
                suspended |= self._suspend(entry, today)
        withdrawn = self.browse()
        for suspension in self.search([('notice_type', '=', 'suspension'), ('state', '=', 'awaiting'),
                                       ('grace_end', '<', today)]):
            withdrawn |= self._withdraw(suspension, today)
        return len(suspended), len(withdrawn)

    # ------------------------------------------------------------------
    # The planning team / Certification Manager act on a suspension
    # ------------------------------------------------------------------
    def action_record_response(self):
        _check_notice_rights(self.env)
        for notice in self:
            if notice.notice_type != 'suspension' or notice.state != 'awaiting':
                raise UserError(_('%s is not awaiting a response.', notice.name))
            if not notice.response_note:
                raise UserError(_('%s: write down what the client answered.', notice.name))
            notice.write({'state': 'responded', 'response_date': fields.Date.context_today(notice)})
            notice.message_post(body=_('Client responded%(date)s: %(note)s - withdrawal stopped.',
                                       date=_(', audit agreed for %s', notice.planned_audit_date)
                                       if notice.planned_audit_date else '', note=notice.response_note))
        return True

    def action_lift(self, reason=None):
        for notice in self:
            if notice.notice_type != 'suspension' or notice.state not in ('awaiting', 'responded'):
                raise UserError(_('%s cannot be lifted.', notice.name))
            note = reason or notice.lift_note
            if not note:
                raise UserError(_('%s: write the reason for lifting the suspension.', notice.name))
            notice.write({'state': 'lifted', 'lift_note': note, 'lifted_on': fields.Date.context_today(notice),
                          'lifted_by': self.env.user.id})
            notice.activity_unlink(['mail.mail_activity_data_todo'])
            if notice.certificate_id.certification_status == 'suspended':
                notice.certificate_id.certification_status = 'active'
            body = _('Suspension %(name)s lifted: %(note)s', name=notice.name, note=note)
            notice.message_post(body=body)
            notice.certificate_id.message_post(body=body)
        return True

    def action_lift_suspension(self):
        _check_notice_rights(self.env)
        return self.action_lift()


class CertificateRegister(models.Model):
    _inherit = 'tuv.certificate.register'

    @api.model
    def _register_certificates(self, certificates):
        created = super()._register_certificates(certificates)
        # the surveillance (or recertification) was held after all: the suspension ends
        Notice = self.env['tuv.certificate.notice'].sudo()
        for entry in created:
            previous_numbers = {entry.name, entry.certificate_id.previous_certificate_id.certificate_number}
            open_suspensions = Notice.search([('notice_type', '=', 'suspension'),
                                              ('state', 'in', ('awaiting', 'responded')),
                                              ('certificate_number', 'in', [n for n in previous_numbers if n])])
            if open_suspensions:
                open_suspensions.action_lift(reason=_('%(type)s certificate %(number)s issued on %(date)s.',
                                                      type=dict(entry._fields['certificate_type'].selection).get(entry.certificate_type),
                                                      number=entry.name, date=entry.issue_date))
        return created
