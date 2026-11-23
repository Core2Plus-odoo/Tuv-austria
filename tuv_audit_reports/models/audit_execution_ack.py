import base64

from odoo import api, fields, models
from odoo.tools import file_open

# project md_audit_type (Mandays tab) -> "Audit type" ticks of the acknowledgement
AUDIT_TYPE_MAP = {
    'certification': 'initial',
    '1st_surveillance': 'surveillance',
    '2nd_surveillance': 'surveillance',
    'recertification': 'recertification',
}
# project payment_status (task 4.3) -> "Payment Status" ticks
PAYMENT_STATUS_MAP = {
    'paid': 'received',
    'partial': 'partial',
    'not_paid': 'not_received',
}


class ProjectProject(models.Model):
    """Audit Execution tab of the project: the "Audit Execution Acknowledgement by Client"
    (FM 04-10, revision 01, 05.12.2022). Every field is filled from the project and stays
    editable; Print gives the form as a PDF."""

    _inherit = 'project.project'

    # 1. Company information: ap_partner_id / ap_company_address (shared audit information)

    # 2. Audit information
    aea_audit_type = fields.Selection([
        ('initial', 'Initial'),
        ('surveillance', 'Surveillance'),
        ('recertification', 'Recertification'),
    ], string='Audit Type', compute='_compute_aea_from_project', store=True, readonly=False)
    aea_date_stage1 = fields.Date(string='Audit Date Stage 1', compute='_compute_aea_from_project',
                                  store=True, readonly=False)
    aea_date_stage2 = fields.Date(string='Audit Date Stage 2', compute='_compute_aea_from_project',
                                  store=True, readonly=False)
    aea_date_surveillance = fields.Date(string='Audit Date Surveillance',
                                        compute='_compute_aea_from_project', store=True, readonly=False)
    aea_date_recert = fields.Date(string='Audit Date Recertification',
                                  compute='_compute_aea_from_project', store=True, readonly=False)
    aea_eac_scope = fields.Char(string='EAC Scope', compute='_compute_aea_from_project',
                                store=True, readonly=False)
    aea_audit_duration = fields.Char(string='Audit Duration', compute='_compute_aea_from_project',
                                     store=True, readonly=False)
    aea_standard_1 = fields.Char(string='Audited Standard 1', compute='_compute_aea_from_project',
                                 store=True, readonly=False)
    aea_standard_2 = fields.Char(string='Audited Standard 2', compute='_compute_aea_from_project',
                                 store=True, readonly=False)
    aea_standard_3 = fields.Char(string='Audited Standard 3', compute='_compute_aea_from_project',
                                 store=True, readonly=False)
    aea_standard_4 = fields.Char(string='Audited Standard 4 (further)',
                                 compute='_compute_aea_from_project', store=True, readonly=False)
    aea_lead_auditor_id = fields.Many2one('res.partner', string='Acknowledgement Lead Auditor',
                                          compute='_compute_aea_from_project', store=True, readonly=False)
    aea_technical_expert_id = fields.Many2one('res.partner', string='Technical Expert',
                                              compute='_compute_aea_from_project', store=True,
                                              readonly=False)
    aea_co_auditor_id = fields.Many2one('res.partner', string='Acknowledgement Co-Auditor',
                                        compute='_compute_aea_from_project', store=True, readonly=False)

    # 3. Signatures
    aea_lead_auditor_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    aea_co_auditor_signature = fields.Binary(string='Co-Auditor(s) Signature', copy=False)
    aea_company_representative = fields.Char(string='Company Representative (Name & Designation)',
                                             compute='_compute_aea_from_project', store=True,
                                             readonly=False)
    aea_company_stamp = fields.Binary(string='Sign & Stamp by Company', copy=False)
    aea_place = fields.Char(string='Acknowledgement Place')
    aea_date = fields.Date(string='Acknowledgement Date')

    # 4. For official use (TUV AUSTRIA Bureau of Inspection & Certification)
    aea_payment_status = fields.Selection([
        ('received', 'Received'),
        ('not_received', 'Not Received'),
        ('partial', 'Partial Payment'),
    ], string='Acknowledgement Payment Status', compute='_compute_aea_official', store=True,
        readonly=False)
    aea_payment_date = fields.Date(string='Payment: Date of Receipt', compute='_compute_aea_official',
                                   store=True, readonly=False)
    aea_payment_signature = fields.Binary(string='Payment: Signature', copy=False)
    aea_sales_tax_invoice = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                             string='Sales Tax Invoice', compute='_compute_aea_official',
                                             store=True, readonly=False)
    aea_sales_tax_invoice_date = fields.Date(string='Sales Tax Invoice: Issue Date',
                                             compute='_compute_aea_official', store=True, readonly=False)
    aea_sales_tax_invoice_signature = fields.Binary(string='Sales Tax Invoice: Signature', copy=False)
    aea_file_received = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                         string='Audit File Received from Auditor')
    aea_file_date = fields.Date(string='Audit File: Date of Receipt')
    aea_file_signature = fields.Binary(string='Audit File: Signature', copy=False)

    @api.depends('md_audit_type', 'ap_audit_date_stage1', 'ap_audit_date_stage2',
                 'md_audit_date_surveillance', 'md_audit_date_recert', 'ea_code_ids',
                 'md_audit_duration', 'ap_standard_line_ids.standard', 'auditor_id',
                 'md_co_auditor_id', 'ap_team_line_ids.partner_id', 'ap_team_line_ids.role',
                 'ap_representative')
    def _compute_aea_from_project(self):
        for project in self:
            project.aea_audit_type = AUDIT_TYPE_MAP.get(project.md_audit_type, False)
            project.aea_date_stage1 = project.ap_audit_date_stage1
            project.aea_date_stage2 = project.ap_audit_date_stage2
            project.aea_date_surveillance = project.md_audit_date_surveillance
            project.aea_date_recert = project.md_audit_date_recert
            project.aea_eac_scope = ', '.join(project.ea_code_ids.mapped('name')) or False
            duration = (project.md_audit_duration or '').strip()
            project.aea_audit_duration = ('%s man-days' % duration) if duration else False
            labels = [line._fields['standard'].convert_to_export(line.standard, line)
                      for line in project.ap_standard_line_ids if line.standard]
            project.aea_standard_1 = labels[0] if labels else False
            project.aea_standard_2 = labels[1] if len(labels) > 1 else False
            project.aea_standard_3 = labels[2] if len(labels) > 2 else False
            project.aea_standard_4 = ', '.join(labels[3:]) or False
            experts = project.ap_team_line_ids.filtered(lambda l: l.role == 'expert')
            project.aea_lead_auditor_id = project.auditor_id
            project.aea_technical_expert_id = experts[:1].partner_id
            project.aea_co_auditor_id = project.md_co_auditor_id
            project.aea_company_representative = project.ap_representative

    @api.depends('payment_status', 'commercial_invoice_ids.payment_state',
                 'sales_tax_invoice_ids.state', 'sales_tax_invoice_ids.issued_on')
    def _compute_aea_official(self):
        for project in self:
            project.aea_payment_status = PAYMENT_STATUS_MAP.get(project.payment_status, False)
            # the latest payment matched with the project's invoices
            invoices = project.commercial_invoice_ids.filtered(lambda m: m.state == 'posted')
            dates = invoices.line_ids.matched_credit_ids.credit_move_id.mapped('date')
            project.aea_payment_date = max(dates) if dates else False
            issued = project.sales_tax_invoice_ids.filtered(lambda s: s.state == 'issued')
            project.aea_sales_tax_invoice = 'yes' if issued else 'no'
            last = max(issued.mapped('issued_on')) if issued else False
            project.aea_sales_tax_invoice_date = last.date() if last else False

    def action_print_execution_acknowledgement(self):
        """Print button of the Audit Execution tab."""
        self.ensure_one()
        # the form brings its own header/footer: no "Configure your document layout" popup
        return self.env.ref('tuv_audit_reports.action_report_audit_execution_ack').with_context(
            discard_logo_check=True).report_action(self)

    def _aea_logo_data_uri(self):
        """The TUV Austria logo with "Bureau of Inspection & Certification", as on FM 04-10."""
        with file_open('tuv_audit_reports/static/src/img/tuv_logo_bic.png', 'rb') as logo:
            return 'data:image/png;base64,' + base64.b64encode(logo.read()).decode()
