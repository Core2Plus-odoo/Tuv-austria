from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# The client hears about the next audit this long before it is due.
REMINDER_MONTHS = 3


class ResCompany(models.Model):
    _inherit = 'res.company'

    ba_team_name = fields.Char(string='BA Team', default='Business Assurance (BA) Team')
    ba_team_contact = fields.Char(string='BA Team Contact Person')
    ba_team_email = fields.Char(string='BA Team Email', help='Left empty: the company e-mail is given.')
    ba_team_phone = fields.Char(string='BA Team Phone', help='Left empty: the company phone is given.')

    def _ba_contact(self):
        """What the client is told to contact: (team, person, e-mail, phone)."""
        self.ensure_one()
        return (self.ba_team_name or _('Business Assurance (BA) Team'), self.ba_team_contact or '',
                self.ba_team_email or self.email or '', self.ba_team_phone or self.phone or '')


class SurveillanceReminder(models.Model):
    """One reminder sent to a client about its next surveillance / recertification audit."""

    _name = 'tuv.surveillance.reminder'
    _description = 'Audit Due Reminder'
    _inherit = ['mail.thread']
    _order = 'due_date, id'

    register_id = fields.Many2one('tuv.certificate.register', string='Register Entry', required=True,
                                  readonly=True, ondelete='restrict', index=True)
    certificate_number = fields.Char(related='register_id.name', store=True, string='Certificate No.')
    partner_id = fields.Many2one('res.partner', string='Client', required=True, readonly=True)
    standards = fields.Char(string='Standard(s)', readonly=True)
    audit_kind = fields.Selection([
        ('surveillance', 'Surveillance Audit'),
        ('recertification', 'Recertification Audit'),
    ], string='Audit Due', required=True, readonly=True)
    due_date = fields.Date(string='Due Date', required=True, readonly=True)
    sent_on = fields.Datetime(string='Sent On', readonly=True)
    email_to = fields.Char(string='Sent To', readonly=True)
    state = fields.Selection([('sent', 'Sent'), ('no_email', 'Not Sent - No E-mail')],
                             string='Status', readonly=True)
    company_id = fields.Many2one('res.company', readonly=True, default=lambda s: s.env.company)

    _one_per_due_date = models.UniqueIndex('(register_id, audit_kind, due_date)')

    def _ba(self):
        return self.company_id._ba_contact()

    @api.model
    def _next_audit(self, entry):
        """(kind, due date) of the next audit of a register entry."""
        if entry.next_surveillance_date:
            return 'surveillance', entry.next_surveillance_date
        if entry.expiry_date:
            return 'recertification', entry.expiry_date
        return False, False

    @api.model
    def _send_for(self, entries, today=None, force=False):
        """Remind the clients whose next audit falls within the reminder window."""
        today = today or fields.Date.context_today(self)
        template = self.env.ref('tuv_austria_customization.mail_template_surveillance_reminder')
        planning = self.env.ref('tuv_austria_customization.group_planning_team')
        planners = self.env['res.users'].search([('all_group_ids', 'in', planning.id)])
        sent = self.browse()
        for entry in entries:
            kind, due = self._next_audit(entry)
            if not due or due < today:
                continue
            if not force and today < due - relativedelta(months=REMINDER_MONTHS):
                continue
            if self.search_count([('register_id', '=', entry.id), ('audit_kind', '=', kind), ('due_date', '=', due)]):
                continue
            client = entry.partner_id
            reminder = self.create({
                'register_id': entry.id, 'partner_id': client.id, 'standards': entry.standards,
                'audit_kind': kind, 'due_date': due, 'sent_on': fields.Datetime.now(),
                'email_to': client.email or False, 'state': 'sent' if client.email else 'no_email',
            })
            if client.email:
                reminder.message_post_with_source(template, partner_ids=client.ids,
                                                  subtype_xmlid='mail.mt_comment', message_type='comment')
            kind_label = dict(self._fields['audit_kind'].selection)[kind]
            body = (_('%(kind)s reminder sent to %(email)s: certificate %(number)s (%(std)s) due %(due)s.',
                      kind=kind_label, email=client.email, number=entry.name, std=entry.standards, due=due)
                    if client.email else
                    _('%(kind)s reminder NOT sent - %(client)s has no e-mail: certificate %(number)s due %(due)s.',
                      kind=kind_label, client=client.name, number=entry.name, due=due))
            cert = entry.certificate_id
            cert.message_post(body=body)
            if cert.project_id:
                cert.project_id.message_post(body=body)
            # the planning team has three months to plan the audit
            for user in planners or self.env.user:
                cert.activity_schedule('mail.mail_activity_data_todo', user_id=user.id, date_deadline=due,
                                       summary=_('Plan the %(kind)s for %(client)s - due %(due)s',
                                                 kind=kind_label.lower(), client=client.name, due=due))
            sent |= reminder
        return sent

    @api.model
    def _cron_send_reminders(self, today=None):
        """Daily: every current, valid certificate whose next audit is 3 months away or closer."""
        entries = self.env['tuv.certificate.register'].search([('is_current', '=', True), ('status', '=', 'valid')])
        return len(self._send_for(entries, today=today))


class TuvCertificate(models.Model):
    _inherit = 'tuv.certificate'

    def action_send_audit_reminder(self):
        """Planning: remind the client now, whatever the date."""
        user = self.env.user
        if not (user.has_group('tuv_austria_customization.group_planning_team') or user.has_group('base.group_system')):
            raise UserError(_('Only the planning team can send an audit reminder.'))
        entries = self.register_ids.filtered(lambda e: e.status == 'valid')
        if not entries:
            raise UserError(_('Only an issued, valid certificate can be reminded about.'))
        sent = self.env['tuv.surveillance.reminder'].sudo()._send_for(entries, force=True)
        if not sent:
            raise UserError(_('A reminder for the next audit of this certificate was already sent.'))
        return True
