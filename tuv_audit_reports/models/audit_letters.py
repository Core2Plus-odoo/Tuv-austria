import base64

from odoo import api, fields, models
from odoo.tools import file_open


class AuditLetterMixin(models.AbstractModel):
    """The three certification letters (forms FM-BA-ZET-MS-All-016-SRVL / -SUSPL / -WDRL):
    the recipient and signatories they share (lt_), then each letter's own fields."""

    _name = 'tuv.audit.letter.mixin'
    _description = 'Certification Letter Fields'

    # recipient
    lt_client_name = fields.Char(string='Client Name')
    lt_client_address = fields.Text(string='Client Address')
    lt_client_contact = fields.Char(string='Client Contact Details')
    lt_attention = fields.Char(string='Attention (Mr. / Mrs.)')
    lt_phone = fields.Char(string='Phone Number')
    lt_standard = fields.Char(string='Standard')
    lt_registration_no = fields.Char(string='Certificate / Registration No. (RGN)')
    # signatories: "NAME / SIGNATURE / POSITION/DPT" in two columns
    lt_signer1_name = fields.Char(string='Signatory 1')
    lt_signer1_position = fields.Char(string='Position / Department 1')
    lt_signer1_signature = fields.Binary(string='Signature 1', copy=False)
    lt_signer2_name = fields.Char(string='Signatory 2')
    lt_signer2_position = fields.Char(string='Position / Department 2')
    lt_signer2_signature = fields.Binary(string='Signature 2', copy=False)

    # Surveillance audit letter (SRVL)
    sv_place = fields.Char(string='Place')
    sv_date = fields.Date(string='Letter Date')
    sv_due_date = fields.Date(string='Surveillance Audit Due Until')
    sv_reply_email = fields.Char(string='Reply by E-mail to')
    sv_reply_fax = fields.Char(string='or Fax to')
    sv_offer_ref = fields.Char(string='Relevant Standard / Offer Number')
    sv_suggested_date = fields.Char(string='Suggested Week and/or Date of Audit')
    sv_changes = fields.Selection([('no', 'No change'), ('yes', 'Yes')], string='Report any Changes')
    sv_changes_text = fields.Text(string='Changes (describe)')
    sv_reply_name = fields.Char(string='Reply: Name')
    sv_reply_position = fields.Char(string='Reply: Position')

    # Suspension letter (SUSPL)
    su_information = fields.Char(string='Information')
    su_date = fields.Date(string='Letter Date')
    su_reason = fields.Char(string='Reason', default='non-conduction of the annual surveillance')
    su_period_from = fields.Date(string='Suspended From')
    su_period_to = fields.Date(string='Suspended Until')

    # Withdrawal letter (WDRL)
    wd_information = fields.Char(string='Information')
    wd_date = fields.Date(string='Letter Date')
    wd_withdrawn_from = fields.Date(string='Permanently Withdrawn From')
    wd_return_address = fields.Char(string='Return the Original Certificates to')
    wd_return_phone = fields.Char(string='Return Address Phone Number')

    def _lt_watermark_data_uri(self):
        """The faint TUV "V" printed behind the letters, as in the Word forms."""
        with file_open('tuv_audit_reports/static/src/img/tuv_watermark.jpeg', 'rb') as img:
            return 'data:image/jpeg;base64,' + base64.b64encode(img.read()).decode()


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = ['tuv.audit.plan', 'tuv.audit.letter.mixin']


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'tuv.audit.letter.mixin']

    # filled from the project, its certificate and its suspension / withdrawal notices
    lt_client_name = fields.Char(compute='_compute_lt_from_project', store=True, readonly=False)
    lt_client_address = fields.Text(compute='_compute_lt_from_project', store=True, readonly=False)
    lt_client_contact = fields.Char(compute='_compute_lt_from_project', store=True, readonly=False)
    lt_attention = fields.Char(compute='_compute_lt_from_project', store=True, readonly=False)
    lt_phone = fields.Char(compute='_compute_lt_from_project', store=True, readonly=False)
    lt_standard = fields.Char(compute='_compute_lt_from_project', store=True, readonly=False)
    lt_registration_no = fields.Char(compute='_compute_lt_from_project', store=True, readonly=False)
    sv_due_date = fields.Date(compute='_compute_lt_dates', store=True, readonly=False)
    su_period_from = fields.Date(compute='_compute_lt_dates', store=True, readonly=False)
    su_period_to = fields.Date(compute='_compute_lt_dates', store=True, readonly=False)
    wd_withdrawn_from = fields.Date(compute='_compute_lt_dates', store=True, readonly=False)

    @api.depends('ap_partner_id', 'ap_company_address', 'ap_representative',
                 'ap_representative_email', 'ap_standards_display', 'certificate_no')
    def _compute_lt_from_project(self):
        for project in self:
            partner = project.ap_partner_id
            project.lt_client_name = partner.name
            project.lt_client_address = '\n'.join(filter(None, (
                line.strip(' ,') for line in (project.ap_company_address or '').split('\n')))) or False
            project.lt_client_contact = ', '.join(filter(None, [
                partner.phone, project.ap_representative_email or partner.email])) or False
            project.lt_attention = project.ap_representative
            project.lt_phone = partner.phone
            project.lt_standard = project.ap_standards_display
            project.lt_registration_no = project.certificate_no

    @api.depends('next_surveillance', 'certificate_ids.next_surveillance_date',
                 'certificate_ids.notice_ids.notice_date', 'certificate_ids.notice_ids.grace_end')
    def _compute_lt_dates(self):
        for project in self:
            certificate = project.certificate_ids.sorted('id')[-1:]
            notices = certificate.notice_ids.sorted('notice_date')
            suspension = notices.filtered(lambda n: n.notice_type == 'suspension')[-1:]
            withdrawal = notices.filtered(lambda n: n.notice_type == 'withdrawal')[-1:]
            project.sv_due_date = certificate.next_surveillance_date or project.next_surveillance
            project.su_period_from = suspension.notice_date
            project.su_period_to = suspension.grace_end
            project.wd_withdrawn_from = withdrawal.notice_date
