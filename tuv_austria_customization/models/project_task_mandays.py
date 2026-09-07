from odoo import api, fields, models

# Option lists taken verbatim from the Word template's content controls
# (FM-BA-ZET-MS-All-003-MDC-EN.docx / KFM-002b Rev.01).
MD_AUDIT_TYPE = [
    ('certification', 'CERTIFICATION'),
    ('1st_surveillance', '1ST SURVEILLANCE'),
    ('2nd_surveillance', '2ND SURVEILLANCE'),
    ('recertification', 'RECERTIFICATION'),
    ('re_audit', 'RE-AUDIT'),
    ('pre_audit', 'PRE-AUDIT'),
    ('extension', 'EXTENSION'),
    ('supplementary', 'SUPPLEMENTARY'),
    ('unannounced', 'UNANNOUNCED'),
    ('short_notice', 'SHORT NOTICE'),
]
MD_AUDIT_KIND = [
    ('combined', 'COMBINED'),
    ('integrated', 'INTEGRATED'),
    ('joint_audit', 'JOINT AUDIT'),
]
MD_AUDIT_LANGUAGE = [
    ('greek', 'GREEK'),
    ('english', 'ENGLISH'),
    ('other', 'OTHER (describe)'),
]
MD_STANDARD = [
    ('iso9001_2015', 'ISO9001:2015'),
    ('iso14001_2015', 'ISO14001:2015'),
    ('iso22000_2018', 'ISO22000:2018'),
    ('iso22000_2005', 'ISO22000:2005'),
    ('fssc22000', 'FSSC22000'),
    ('ohsas18001', 'OHSAS18001'),
    ('iso45001', 'ISO45001'),
    ('iso27001', 'ISO27001'),
    ('iso22301', 'ISO22301'),
    ('iso50001', 'ISO50001'),
    ('iso39001', 'ISO39001'),
    ('iso13485', 'ISO13485'),
    ('emas_iii', 'EMAS III'),
    ('iso_iec20000', 'ISO/IEC20000'),
    ('globalgap', 'GLOBALGAP'),
    ('iso37001', 'ISO37001'),
    ('en15224_2016', 'EN15224:2016'),
    ('iso22716', 'ISO22716'),
]
MD_FSSC = [
    ('ts22002_1', 'ISO/TS 22002-1, FSSC 22000 Additional requirements, ISO 22000:2018,'),
    ('ts22002_2', 'ISO/TS 22002-2, FSSC 22000 Additional requirements, ISO 22000:2018'),
    ('ts22002_4', 'ISO/TS 22002-4, FSSC 22000 Additional requirements, ISO 22000:2018'),
    ('pas221', 'BSI/PAS 221:2013, FSSC 22000 Additional requirements, ISO 22000:2018'),
]
MD_RISK_LEVEL = [
    ('high', 'HIGH'),
    ('medium', 'MEDIUM'),
    ('low', 'LOW'),
]


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # ==================================================================
    # COMPANY INFORMATION - owned by the order/customer, shown read-only
    # ==================================================================
    md_company_name = fields.Char(
        related='partner_id.name', string='Company Name', readonly=True)
    md_street = fields.Char(related='partner_id.street', string='Street', readonly=True)
    md_street2 = fields.Char(related='partner_id.street2', string='Street 2', readonly=True)
    md_city = fields.Char(related='partner_id.city', string='City', readonly=True)
    md_zip = fields.Char(related='partner_id.zip', string='ZIP', readonly=True)
    md_state_id = fields.Many2one(related='partner_id.state_id', string='State', readonly=True)
    md_country_id = fields.Many2one(related='partner_id.country_id', string='Country', readonly=True)
    md_other_sites = fields.Char(
        related='sale_order_id.other_facilities',
        string='Other audited sites (permanent or temporary)', readonly=True)
    md_company_representative = fields.Char(
        related='sale_order_id.company_representative',
        string='Company Representative', readonly=True)
    md_company_description = fields.Text(
        string='Description of the company',
        help='Number of personnel, basic business processes, commercial activities, '
             'brief history.')

    # ==================================================================
    # AUDIT INFORMATION
    # ==================================================================
    md_audit_date_st1 = fields.Date(string='Audit date St.1')
    md_audit_date_st2 = fields.Date(string='Audit date St.2')
    md_audit_date_surveillance = fields.Date(
        string='Audit date Surveillance', compute='_compute_md_from_order',
        store=True, readonly=False)
    md_audit_date_recert = fields.Date(string='Audit date Recertification')
    md_audit_duration = fields.Char(string='Audit Duration (Mandays)')
    md_certification_scope = fields.Char(
        related='sale_order_id.scope_of_certification',
        string='Certification Scope', readonly=True)
    # EA CODE reuses the task's own ea_code_ids field
    md_nace = fields.Char(string='NACE')
    md_category = fields.Char(string='Category')
    md_other_code = fields.Char(string='Other (code)')
    md_remote_auditing = fields.Text(string='Use of remote auditing activities (describe)')
    md_audit_type = fields.Selection(MD_AUDIT_TYPE, string='Audit type')
    md_audit_kind = fields.Selection(MD_AUDIT_KIND, string='Audit Kind')
    md_audit_language = fields.Selection(MD_AUDIT_LANGUAGE, string='Audit language')
    md_standard_1 = fields.Selection(MD_STANDARD, string='Standard 1')
    md_standard_2 = fields.Selection(MD_STANDARD, string='Standard 2')
    md_standard_3 = fields.Selection(MD_STANDARD, string='Standard 3')
    md_standard_other = fields.Char(string='Covered Standards - Other')
    md_fssc_22000 = fields.Selection(MD_FSSC, string='For FSSC 22000')

    # ==================================================================
    # AUDIT TEAM  (LA reuses the task's own auditor_id)
    # ==================================================================
    md_co_auditor_id = fields.Many2one(
        'res.partner', string='CA (Co-Auditor)',
        domain="[('contact_type', '=', 'auditor')]")
    md_trainee_id = fields.Many2one(
        'res.partner', string='TR (Trainee)',
        domain="[('contact_type', '=', 'auditor')]")
    md_other_participants = fields.Char(
        string='Other participants (observers, interpreters, experts etc)')

    # ==================================================================
    # ANNEX I - Individual Management Systems, Manday Calculation
    # ==================================================================
    md1_applicable_system = fields.Char(
        string='Applicable Management System', compute='_compute_md_from_order',
        store=True, readonly=False)
    md1_complexity_ranking = fields.Char(string='Complexity / risk Ranking')
    md1_justification = fields.Text(string='Justification of Reduced Complexity / Risk')
    md1_total_personnel = fields.Char(string='Total number of Personnel')
    md1_employees_on_shifts = fields.Char(
        string='Number of employees on shifts', compute='_compute_md_from_order',
        store=True, readonly=False)
    md1_employees_without_shifts = fields.Char(string='Number of employees without shifts')
    md1_number_of_shifts = fields.Char(
        string='Number of shifts', compute='_compute_md_from_order',
        store=True, readonly=False)
    md1_permanent_contracted = fields.Char(
        string='Permanent contracted personnel', compute='_compute_md_from_order',
        store=True, readonly=False)
    md1_seasonal = fields.Char(string='Seasonal personnel')
    md1_part_time = fields.Char(string='Part time personnel (including contracted personnel)')
    md1_months_employment = fields.Char(string='Months of employment')
    md1_temporary_unskilled = fields.Char(
        string='Temporary unskilled personnel', compute='_compute_md_from_order',
        store=True, readonly=False)
    md1_equivalent_personnel = fields.Char(string='Equivalent number of personnel')
    md1_final_md = fields.Char(string='Final MD calculation based on the relevant table')
    md1_ds_equation = fields.Char(string='Ds =')
    md1_c_equation = fields.Char(string='C =')
    md1_activity_name = fields.Char(string='Name of the activity')
    md1_activity_personnel = fields.Char(string='Number of personnel for this activity')
    md1_personnel_reduction = fields.Char(string='Reduction of the number of personnel')
    md1_non_repetitive = fields.Boolean(string='Non Repetitive activity')
    md1_repetitive = fields.Boolean(string='Repetitive activity')
    md1_risk_level = fields.Selection(MD_RISK_LEVEL, string='Risk level')
    md1_remaining_personnel = fields.Char(
        string='Remaining number of personnel used to calculate the Equivalent number '
               'of personnel')
    md1_other_standard = fields.Char(string='Other standard (fill in)')
    md1_final_mandays = fields.Char(string='Final mandays calculation')
    md1_observations = fields.Text(string='Observations (Annex I)')

    # ==================================================================
    # ANNEX II - Integrated Management Systems
    # ==================================================================
    md2_applicable_system = fields.Char(string='Applicable Management System (Annex II)')
    md2_total_personnel = fields.Char(string='Total number of Personnel (Annex II)')
    md2_employees_on_shifts = fields.Char(string='Number of employees on shifts (Annex II)')
    md2_employees_without_shifts = fields.Char(
        string='Number of employees without shifts (Annex II)')
    md2_number_of_shifts = fields.Char(string='Number of shifts (Annex II)')
    md2_permanent_contracted = fields.Char(string='Permanent contracted personnel (Annex II)')
    md2_seasonal = fields.Char(string='Seasonal personnel (Annex II)')
    md2_part_time = fields.Char(string='Part time personnel (Annex II)')
    md2_months_employment = fields.Char(string='Months of employment (Annex II)')
    md2_temporary_unskilled = fields.Char(string='Temporary unskilled personnel (Annex II)')
    md2_equivalent_personnel = fields.Char(string='Equivalent number of personnel (Annex II)')

    md2_sys1_complexity = fields.Char(string='System 1 - Complexity / Risk Ranking')
    md2_sys1_mandays = fields.Char(string='System 1 - Man-Days according to relevant table')
    md2_sys2_complexity = fields.Char(string='System 2 - Complexity / Risk Ranking')
    md2_sys2_mandays = fields.Char(string='System 2 - Man-Days according to relevant table')
    md2_sys3_complexity = fields.Char(string='System 3 - Complexity / Risk Ranking')
    md2_sys3_mandays = fields.Char(string='System 3 - Man-Days according to relevant table')
    md2_sys4_complexity = fields.Char(string='System 4 - Complexity / Risk Ranking')
    md2_sys4_mandays = fields.Char(string='System 4 - Man-Days according to relevant table')

    md2_inc_sys1 = fields.Char(string='Increase - System 1')
    md2_inc_sys1_pct = fields.Char(string='Increase % - System 1')
    md2_inc_sys2 = fields.Char(string='Increase - System 2')
    md2_inc_sys2_pct = fields.Char(string='Increase % - System 2')
    md2_inc_sys3 = fields.Char(string='Increase - System 3')
    md2_inc_sys3_pct = fields.Char(string='Increase % - System 3')
    md2_inc_sys4 = fields.Char(string='Increase - System 4')
    md2_inc_sys4_pct = fields.Char(string='Increase % - System 4')

    md2_dec_sys1 = fields.Char(string='Decrease - System 1')
    md2_dec_sys1_pct = fields.Char(string='Decrease % - System 1')
    md2_dec_sys2 = fields.Char(string='Decrease - System 2')
    md2_dec_sys2_pct = fields.Char(string='Decrease % - System 2')
    md2_dec_sys3 = fields.Char(string='Decrease - System 3')
    md2_dec_sys3_pct = fields.Char(string='Decrease % - System 3')
    md2_dec_sys4 = fields.Char(string='Decrease - System 4')
    md2_dec_sys4_pct = fields.Char(string='Decrease % - System 4')

    # ==================================================================
    # FINAL M/D CALCULATION (Method 1 / Method 2)
    # ==================================================================
    md4_sys1_md = fields.Char(string='A = (System 1)')
    md4_sys2_md = fields.Char(string='B = (System 2)')
    md4_sys3_md = fields.Char(string='C = (System 3)')
    md4_sys4_md = fields.Char(string='D = (System 4)')
    md4_level_of_integration = fields.Selection(
        [(str(pct), '%d%%' % pct) for pct in range(10, 101, 10)],
        string='Level of integration %', compute='_compute_md_from_order',
        store=True, readonly=False)
    md4_due_to_1 = fields.Char(string='Due to (1)')
    md4_due_to_2 = fields.Char(string='Due to (2)')
    md4_combined_audit_pct = fields.Char(string='Ability to perform combined audit %')

    md4_sys1_cert = fields.Char(string='System 1 - Certification / re-Certification')
    md4_sys2_cert = fields.Char(string='System 2 - Certification / re-Certification')
    md4_sys3_cert = fields.Char(string='System 3 - Certification / re-Certification')
    md4_sys4_cert = fields.Char(string='System 4 - Certification / re-Certification')
    md4_sys1_surv1 = fields.Char(string='System 1 - 1st surveillance')
    md4_sys2_surv1 = fields.Char(string='System 2 - 1st surveillance')
    md4_sys3_surv1 = fields.Char(string='System 3 - 1st surveillance')
    md4_sys4_surv1 = fields.Char(string='System 4 - 1st surveillance')
    md4_sys1_surv2 = fields.Char(string='System 1 - 2nd surveillance')
    md4_sys2_surv2 = fields.Char(string='System 2 - 2nd surveillance')
    md4_sys3_surv2 = fields.Char(string='System 3 - 2nd surveillance')
    md4_sys4_surv2 = fields.Char(string='System 4 - 2nd surveillance')

    md4_total_md = fields.Char(string='Total - M/D after decrease / increase')
    md4_total_pct = fields.Char(string='Total - % of decrease')
    md4_total_cert = fields.Char(string='Total - Certification / re-Certification')
    md4_total_surv1 = fields.Char(string='Total - 1st surveillance')
    md4_total_surv2 = fields.Char(string='Total - 2nd surveillance')

    md4_t_equation = fields.Char(string='T = A + 0,5 B + 0,5 C + 0,5 D')
    md4_observations = fields.Text(string='Observations (Final M/D)')
    md4_lead_auditor = fields.Char(string='Lead auditor (sign-off)')
    md4_date = fields.Date(string='Date (sign-off)')
    md4_signature = fields.Binary(string='Signature', attachment=True)
    md4_signature_filename = fields.Char(string='Signature Filename')

    # ------------------------------------------------------------------
    # Values the sale order already carries. They are computed so the task
    # is pre-filled, but stored and readonly=False so the auditor can
    # override them for the man-day calculation without touching the order.
    # ------------------------------------------------------------------
    @api.depends('sale_order_id')
    def _compute_md_from_order(self):
        for task in self:
            order = task.sale_order_id
            task.md_audit_date_surveillance = order.next_surveillance or False
            task.md1_applicable_system = order.management_system_name or False
            task.md1_employees_on_shifts = order.personnel_on_shifts or False
            task.md1_number_of_shifts = order.number_of_shifts or False
            task.md1_permanent_contracted = order.permanent_personnel or False
            task.md1_temporary_unskilled = order.temporary_personnel or False
            task.md4_level_of_integration = order.level_of_integration or False
