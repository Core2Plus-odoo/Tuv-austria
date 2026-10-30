from odoo import Command, api, fields, models

from .audit_expert_report import expert_requirement_commands
from .audit_plan import AUDIT_TYPES, STANDARDS, TEAM_ROLES

# Smaller forms of the accreditation bodies:
#   ESYD  certificate text FM-BA-ZET-MS-All-013-CT-EN            (ect_)
#   PNAC  certificate text TUV/BA/FM/04-2                         (pct_)
#   PNAC  client response form TUV/BA/FM/09-1                     (pcr_)
#   PNAC  technical expert report = TUV form FM-TAGMBH-MSZ-004    (er_ fields of audit_expert_report)
#   SAAC  participation list FM-BA-ZET-MS-All-012-TNL             (pl_ fields of audit_participation)
#   SAAC  auditor assignment FM-BA-ZET-MS-All-007-AAS-EN          (saa_)
#   SAAC  audit program FM-BA-ZET-MS-All-008-AT-EN                (sapg_)

YES_NO = [('yes', 'YES'), ('no', 'NO')]

# ESYD certificate text: the "Applicable standard" grid (2 rows of 3, then a free cell per row)
ECT_STANDARDS = [
    ('ect_std_iso9001', 'ISO 9001', ('iso_9001_2015',)),
    ('ect_std_iso22000', 'ISO 22000', ('iso_22000_2018', 'fssc_22000')),
    ('ect_std_iso27001', 'ISO/IEC 27001', ('iso_27001_2013', 'iso_27001_2022')),
    ('ect_std_iso14001', 'ISO 14001', ('iso_14001_2015',)),
    ('ect_std_iso45001', 'ISO 45001', ('iso_45001_2018',)),
    ('ect_std_iso20000', 'ISO/IEC 20000', ('iso_20000_1_2018',)),
]
# PNAC certificate text: the same grid with "Others" and a free box instead of 27001 / 20000
PCT_STANDARDS = [
    ('pct_std_iso9001', 'ISO 9001', ('iso_9001_2015',)),
    ('pct_std_iso22000', 'ISO 22000', ('iso_22000_2018', 'fssc_22000')),
    ('pct_std_iso14001', 'ISO 14001', ('iso_14001_2015',)),
    ('pct_std_iso45001', 'ISO 45001', ('iso_45001_2018',)),
]
# "Special requirements" rows of the GLOBALG.A.P. table (ESYD certificate text)
ECT_GGAP_ROWS = ['Parallel Production', 'Parallel Ownership', 'Harvest', 'Produce Handling']

# PNAC client response form: the criteria of sections 1 and 2, one rating field each
PCR_RATINGS = [
    ('excellent', 'Excellent'),
    ('good', 'Good'),
    ('satisfactory', 'Satisfactory'),
    ('needs_improvement', 'Needs Improvement'),
]
PCR_CONDUCT = [
    ('pcr_rate_behavior', 'Professional behavior and ethics'),
    ('pcr_rate_communication', 'Communication with auditee'),
    ('pcr_rate_protocols', 'Respect for organizational protocols'),
]
PCR_EXECUTION = [
    ('pcr_rate_knowledge', 'Knowledge of relevant ISO standard'),
    ('pcr_rate_planning', 'Audit planning and preparation'),
    ('pcr_rate_objectivity', 'Objectivity and impartiality'),
    ('pcr_rate_findings', 'Effectiveness of audit findings and observations'),
    ('pcr_rate_time', 'Time management during the audit'),
]

# SAAC audit program: the five audit columns (field prefix, heading)
SAPG_STAGES = [
    ('stage1', 'STAGE 1'),
    ('stage2', 'STAGE 2'),
    ('surv1', '1. SURVEILLANCE'),
    ('surv2', '2. SURVEILLANCE'),
    ('recert', 'RECERTIFICATION'),
]
# clauses of the first standard of every column, then the 8 rows left free for the second
SAPG_CLAUSES = ['4.1', '4.2', '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '6.1', '6.2', '6.3', '6.4',
                '7.1', '7.2', '7.3', '7.4', '7.5', '7.6', '8.1', '8.2', '8.3', '8.4', '8.5'] + [''] * 8
SAPG_QUESTIONS = [
    ('CHANGES', True),
    ('Is the number of employees the same?', False),
    ('Are Scope and Codes the same?', False),
    ('Are the Title and Addresses the same?', False),
    ('Have there been any changes in the accreditation conditions?', False),
    ('Are there any changes to your Business Legal Terms?', False),
    ('Is the integration level the same?', False),
    ('Customer complaints and related party expectations', False),
    ('COMPANY PERFORMANCE DATA', True),
    ('Detected small app. number:', False),
    ('Detected large app. number:', False),
    ('Have all non-conformances been closed? Is it active?', False),
    ('Are there any contradictions in the use of Logo and Certificate?', False),
]
# md_audit_type of the project -> the audit program column it belongs to
SAPG_STAGE_BY_AUDIT = {
    'certification': ('stage1', 'stage2'),
    '1st_surveillance': ('surv1',),
    '2nd_surveillance': ('surv2',),
    'recertification': ('recert',),
}


def ect_ggap_commands():
    return [Command.create({'sequence': 10 * (i + 1), 'name': name})
            for i, name in enumerate(ECT_GGAP_ROWS)]


def sapg_item_commands():
    return [Command.create({'sequence': 10 * (i + 1), 'clause': clause or False})
            for i, clause in enumerate(SAPG_CLAUSES)]


def sapg_question_commands():
    return [Command.create({'sequence': 10 * (i + 1), 'name': name, 'is_section': section})
            for i, (name, section) in enumerate(SAPG_QUESTIONS)]


def _fmt_date(value):
    return value.strftime('%d.%m.%Y') if value else ''


def _address_lines(project):
    return [line.strip(' ,') for line in (project.ap_company_address or '').split('\n')
            if line.strip(' ,')]


def _audit_dates_text(project):
    """'dd.mm.yyyy, dd.mm.yyyy - dd.mm.yyyy' from the audit dates of section 2."""
    days = ', '.join(filter(None, [_fmt_date(project.ap_audit_date_stage1),
                                   _fmt_date(project.ap_audit_date_stage2)]))
    if days and project.ap_audit_date_until:
        days += ' - ' + _fmt_date(project.ap_audit_date_until)
    return days or False


def _standard_labels(project):
    labels = dict(STANDARDS)
    return [labels[s] for s in project.ap_standard_line_ids.mapped('standard') if s]


def _head_office_commands(project):
    """One head office row of a certificate text: company, address and scope of the project."""
    text = '\n'.join(filter(None, [project.ap_partner_id.name] + _address_lines(project)))
    if not (text or project.ap_certificate_scope):
        return []
    return [Command.create({'sequence': 10, 'language': 'English', 'company_text': text or False,
                            'scope': project.ap_certificate_scope or False, 'a4': True})]


def _site_commands(project):
    """A row per other audited site (one per line of the project's other sites, at most 3)."""
    sites = [s.strip() for s in (project.ap_other_sites or '').split('\n') if s.strip()]
    return [Command.create({'sequence': 10 * (i + 1), 'language': 'English', 'company_text': site,
                            'a4': True}) for i, site in enumerate(sites[:3])]


def _rows(lines, count):
    """The lines, then blank rows up to the rows of the Word table."""
    rows = list(lines)
    return rows + [False] * max(0, count - len(rows))


# ----------------------------------------------------------------------
# Line models
# ----------------------------------------------------------------------
class FormCtAddressMixin(models.AbstractModel):
    """A row of the "Address of Head Office" / "Address of other sites" tables of the
    ESYD and PNAC certificate texts."""

    _name = 'tuv.form.ct.address.mixin'
    _description = 'Certificate Text Address Row'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    language = fields.Char(string='Language')
    company_text = fields.Text(string="Company's Name, P.C., Address, Country")
    scope = fields.Text(string='Certified Scope')
    a3 = fields.Boolean(string='A3')
    a4 = fields.Boolean(string='A4')


class FormEctAddress(models.Model):
    _name = 'tuv.form.ect.address'
    _inherit = 'tuv.form.ct.address.mixin'
    _description = 'ESYD Certificate Text Address'

    # one inverse per table: head office rows, other site rows
    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    site_plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    site_project_id = fields.Many2one('project.project', ondelete='cascade', index=True)


class FormPctAddress(models.Model):
    _name = 'tuv.form.pct.address'
    _inherit = 'tuv.form.ct.address.mixin'
    _description = 'PNAC Certificate Text Address'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    site_plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    site_project_id = fields.Many2one('project.project', ondelete='cascade', index=True)


class FormEctGgapLine(models.Model):
    """A "Special requirements" row of the GLOBALG.A.P. table (ESYD certificate text)."""

    _name = 'tuv.form.ect.ggap.line'
    _description = 'ESYD Certificate Text GLOBALG.A.P. Requirement'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Valid for the Operation')
    company_text = fields.Text(string='Company Name and Address, sub-GLN or GGN (PMU / PHU)')
    products = fields.Text(string='Products and Description where required')
    valid = fields.Selection(YES_NO, string='Yes / No')


class FormSapgItem(models.Model):
    """A row of the "Items to be Examined" grid of the SAAC audit program. Per audit column:
    the first standard's clause (fixed) with its box, then a box and a free clause for the
    second standard."""

    _name = 'tuv.form.sapg.item'
    _description = 'SAAC Audit Program Item'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    clause = fields.Char(string='Clause')
    stage1_a = fields.Boolean(string='St.1')
    stage1_b = fields.Boolean(string='St.1 Std 2')
    stage1_b_clause = fields.Char(string='St.1 Std 2 Clause')
    stage2_a = fields.Boolean(string='St.2')
    stage2_b = fields.Boolean(string='St.2 Std 2')
    stage2_b_clause = fields.Char(string='St.2 Std 2 Clause')
    surv1_a = fields.Boolean(string='Surv.1')
    surv1_b = fields.Boolean(string='Surv.1 Std 2')
    surv1_b_clause = fields.Char(string='Surv.1 Std 2 Clause')
    surv2_a = fields.Boolean(string='Surv.2')
    surv2_b = fields.Boolean(string='Surv.2 Std 2')
    surv2_b_clause = fields.Char(string='Surv.2 Std 2 Clause')
    recert_a = fields.Boolean(string='Recert.')
    recert_b = fields.Boolean(string='Recert. Std 2')
    recert_b_clause = fields.Char(string='Recert. Std 2 Clause')


class FormSapgQuestion(models.Model):
    """A row of the "CHANGES" / "COMPANY PERFORMANCE DATA" part of the SAAC audit program:
    the question, then an answer per audit column."""

    _name = 'tuv.form.sapg.question'
    _description = 'SAAC Audit Program Question'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    is_section = fields.Boolean(string='Heading')
    name = fields.Char(string='Question')
    stage1 = fields.Char(string='Stage 1')
    stage2 = fields.Char(string='Stage 2')
    surv1 = fields.Char(string='1. Surveillance')
    surv2 = fields.Char(string='2. Surveillance')
    recert = fields.Char(string='Recertification')


# ----------------------------------------------------------------------
# Form fields
# ----------------------------------------------------------------------
class AccSmallFormsMixin(models.AbstractModel):
    """Fields of the smaller ESYD / PNAC / SAAC forms (the o2m tables are declared per model)."""

    _name = 'tuv.acc.small.forms.mixin'
    _description = 'Accreditation Body Forms (Certificate Texts, Client Response, Assignment, Program)'

    # ===== ESYD certificate text (FM-BA-ZET-MS-All-013-CT-EN) =====
    ect_std_iso9001 = fields.Boolean(string='ISO 9001')
    ect_std_iso22000 = fields.Boolean(string='ISO 22000')
    ect_std_iso27001 = fields.Boolean(string='ISO/IEC 27001')
    ect_std_iso14001 = fields.Boolean(string='ISO 14001')
    ect_std_iso45001 = fields.Boolean(string='ISO 45001')
    ect_std_iso20000 = fields.Boolean(string='ISO/IEC 20000')
    ect_std_other_1 = fields.Char(string='Other Standard 1')
    ect_std_other_2 = fields.Char(string='Other Standard 2')
    ect_trademark = fields.Selection(YES_NO, string='Include the Registered Trademark on the Certificate')
    ect_legislation = fields.Selection(YES_NO, string='The Scope Refers to Legislation')
    ect_subcontracted = fields.Selection(YES_NO, string='The Scope Refers to Subcontracted Processes')
    ect_place = fields.Char(string='Place')
    ect_date = fields.Date(string='Date')
    ect_lead_auditor_id = fields.Many2one('res.partner', string='Lead Auditor')
    ect_lead_auditor_signature = fields.Binary(string='Signature of Lead Auditor', copy=False)
    ect_company_signature = fields.Binary(string='Signature and Stamp of Company Representative',
                                          copy=False)
    ect_rep_phone = fields.Char(string='Company Representative Tel')
    ect_rep_email = fields.Char(string='Company Representative Email')
    # IFS certificates - additional information
    ect_ifs_coid = fields.Char(string='COID')
    ect_ifs_product_scopes = fields.Char(string='Product Scopes')
    ect_ifs_exclusions = fields.Char(string='Exclusions')
    ect_ifs_technology_scopes = fields.Char(string='Technology Scopes')
    ect_ifs_audit_result = fields.Char(string='Audit Result')
    ect_ifs_audit_dates = fields.Char(string='Audit Date(s)')
    ect_ifs_issue_date = fields.Date(string='Certificate Issue Date')
    ect_ifs_valid_until = fields.Date(string='Certificate Valid Until')
    ect_ifs_next_period = fields.Char(string='Next Audit Period')
    ect_ifs_outsourcing = fields.Char(string='Outsourcing')
    ect_ifs_unannounced = fields.Char(string='Unannounced')
    # GLOBALG.A.P. certificates - additional information
    ect_gg_version = fields.Char(string='Version', help='The exact version of the standard, e.g. 5-x-y_month_year')
    ect_gg_opt1_individual = fields.Boolean(string='OPTION 1 – Individual Producer')
    ect_gg_opt2_group = fields.Boolean(string='OPTION 2 – Producer Group')
    ect_gg_opt1_multi_qms = fields.Boolean(string='OPTION 1 – Individual multisite producer with QMS')
    ect_gg_opt1_multi_no_qms = fields.Boolean(string='OPTION 1 – Individual multisite producer without a QMS')
    ect_gg_coc_fruits = fields.Boolean(string='Chain of Custody – Fruits and vegetables')
    ect_gg_coc_aquaculture = fields.Boolean(string='Chain of Custody – Aquaculture')
    ect_gg_cfm = fields.Boolean(string='Compound Feed Manufacturing')
    ect_gg_grasp = fields.Boolean(string='GRASP')
    ect_gg_standardization = fields.Selection(YES_NO, string='Chain of Custody: Standardization')
    ect_gg_gfsi = fields.Selection(YES_NO, string='Chain of Custody: GFSI Scheme')
    ect_gg_total_employees = fields.Char(string='GRASP: Total Number of Employees')
    ect_gg_rural_employees = fields.Char(string='GRASP: Number of Employees on Rural Production')
    ect_gg_packaging_employees = fields.Char(string='GRASP: Number of Employees on Packaging')
    ect_gg_local = fields.Boolean(string='GRASP: Local')
    ect_gg_migrants = fields.Boolean(string='GRASP: Migrants')
    ect_gg_annex_members = fields.Boolean(string='Annex: Group Member Producers')
    ect_gg_annex_packaging = fields.Boolean(string='Annex: Packaging & Handling Facilities')
    ect_gg_annex_sites = fields.Boolean(string='Annex: Production Sites')
    ect_gg_online_group = fields.Selection(
        YES_NO, string='Data Online: Name, Surname, Address, PO, Group Country')
    ect_gg_online_producer = fields.Selection(
        YES_NO, string='Data Online: Name, Surname, Address, PO, Producer Country')

    # ===== PNAC certificate text (TUV/BA/FM/04-2) =====
    pct_std_iso9001 = fields.Boolean(string='ISO 9001')
    pct_std_iso22000 = fields.Boolean(string='ISO 22000')
    pct_std_iso14001 = fields.Boolean(string='ISO 14001')
    pct_std_iso45001 = fields.Boolean(string='ISO 45001')
    pct_std_others = fields.Boolean(string='Others')
    pct_std_others_text = fields.Char(string='Others (Standard)')
    pct_std_other2 = fields.Boolean(string='Other Standard 2')
    pct_std_other2_text = fields.Char(string='Other Standard 2 (Name)')
    pct_trademark = fields.Selection(YES_NO, string='Include the Registered Trademark on the Certificate')
    pct_legislation = fields.Selection(YES_NO, string='The Scope Refers to Legislation')
    pct_subcontracted = fields.Selection(YES_NO, string='The Scope Refers to Subcontracted Processes')
    pct_place = fields.Char(string='Place')
    pct_date = fields.Date(string='Date')
    pct_lead_auditor_id = fields.Many2one('res.partner', string='Lead Auditor')
    pct_lead_auditor_signature = fields.Binary(string='Signature of Lead Auditor', copy=False)
    pct_company_signature = fields.Binary(string='Signature and Stamp of Company Representative',
                                          copy=False)
    pct_rep_phone = fields.Char(string='Company Representative Tel')
    pct_rep_email = fields.Char(string='Company Representative Email')

    # ===== PNAC client response form (TUV/BA/FM/09-1) =====
    pcr_client_name = fields.Char(string='Client Name')
    pcr_audit_dates = fields.Char(string='Audit Date(s)')
    pcr_auditor_name = fields.Char(string='Lead Auditor / Auditor Name')
    pcr_standard = fields.Char(string='Standard Audited')
    pcr_rate_behavior = fields.Selection(PCR_RATINGS, string='Professional behavior and ethics')
    pcr_rate_communication = fields.Selection(PCR_RATINGS, string='Communication with auditee')
    pcr_rate_protocols = fields.Selection(PCR_RATINGS, string='Respect for organizational protocols')
    pcr_rate_knowledge = fields.Selection(PCR_RATINGS, string='Knowledge of relevant ISO standard')
    pcr_rate_planning = fields.Selection(PCR_RATINGS, string='Audit planning and preparation')
    pcr_rate_objectivity = fields.Selection(PCR_RATINGS, string='Objectivity and impartiality')
    pcr_rate_findings = fields.Selection(PCR_RATINGS,
                                         string='Effectiveness of audit findings and observations')
    pcr_rate_time = fields.Selection(PCR_RATINGS, string='Time management during the audit')
    pcr_effective = fields.Text(string="What aspects of the auditor's performance were most effective?")
    pcr_improvement = fields.Text(string='Were there any areas where the audit could have been improved?')
    pcr_comments = fields.Text(string='Additional comments or feedback')
    pcr_completed_by = fields.Char(string='Completed by')
    pcr_position = fields.Char(string='Position')
    pcr_signature = fields.Binary(string='Signature', copy=False)
    pcr_date = fields.Date(string='Date')

    # ===== SAAC auditor assignment (FM-BA-ZET-MS-All-007-AAS-EN) =====
    saa_auditor_id = fields.Many2one('res.partner', string='Name of Auditor')
    saa_assignment = fields.Char(string='Assignment',
                                 help='Audit Assignment_Client name_Standard_Version_Type of Audit')
    saa_client = fields.Char(string='Client')
    saa_standards = fields.Char(string='Standard(s) / Version')
    saa_certificate_numbers = fields.Char(string='Certificate Number(s)')
    saa_accreditation = fields.Char(string='Accreditation', default='SAAC')
    saa_audit_type = fields.Char(string='Audit Type')
    saa_decision_release = fields.Char(string='Certification Decision / Release')
    saa_other_info = fields.Text(string='Other Important Information')
    saa_possible_scope = fields.Text(string='Possible Scope during Application')
    saa_location = fields.Text(string='Location')
    saa_audit = fields.Char(string='Audit')
    saa_order = fields.Char(string='Order')
    saa_offer = fields.Char(string='Offer')
    saa_client_address = fields.Text(string='Client Address')
    saa_client_contact = fields.Char(string='Client Contact Information')
    saa_client_contact_persons = fields.Char(string='Client Contact Persons')
    saa_audit_scopes = fields.Text(string='Audit Scopes (to be confirmed during the audit)')
    saa_client_relationship = fields.Char(string='Client Relationship')
    saa_personnel = fields.Char(string='Number of Personnel (to be confirmed during the audit)')
    saa_client_additional = fields.Text(string='Client Additional Data')
    saa_audit_team = fields.Text(string='Audit Team')
    saa_duration = fields.Char(string='Duration in Days (Hours)')
    saa_payment = fields.Char(string='External Auditors Payment (€)')
    saa_additional_costs = fields.Selection(
        [('included', 'Included'), ('excluded', 'Excluded')],
        string='Additional Costs (Accommodation, Tickets, Transfer, etc.)')
    saa_confirmed = fields.Boolean(
        string='I hereby confirm the compliance to the above-mentioned regulations of TÜV AUSTRIA')
    saa_contact_user = fields.Char(string='For Further Questions Please Contact')
    saa_contact_phone = fields.Char(string='Phone')
    saa_contact_email = fields.Char(string='E-mail')
    saa_contact_web = fields.Char(string='Web')

    # ===== SAAC audit program (FM-BA-ZET-MS-All-008-AT-EN) =====
    sapg_company_name = fields.Char(string='Company Name')
    sapg_addresses = fields.Text(string='Company Addresses (Headquarters, Branch, Factory, Construction Site)')
    sapg_scope = fields.Text(string='Scope')
    sapg_non_applicable = fields.Char(string='Non-Applicable Substance(s)')
    sapg_ea_nace = fields.Char(string='EA/NACE Code')
    sapg_category = fields.Char(string='Category')
    sapg_employees = fields.Char(string='Number of Employees')
    sapg_shift_employees = fields.Char(string='Shift and Number of Employees')
    sapg_standards = fields.Char(string='Standard / Standards')
    sapg_committee_decision = fields.Char(string='Committee Decision')
    sapg_others = fields.Char(string='Others')
    sapg_branch_employees = fields.Char(string='Number of Branch Employees')
    sapg_audit_responsible = fields.Char(string='Company Audit Responsible')
    sapg_certificate = fields.Char(string='Certificate No and Exchange Date')
    # one block per audit column (stage 1, stage 2, 1./2. surveillance, recertification)
    sapg_stage1_employees = fields.Char(string='Stage 1: Total Number of Employees')
    sapg_stage1_risk = fields.Char(string='Stage 1: Risk / Complexity Rate')
    sapg_stage1_std1 = fields.Char(string='Stage 1: Standard 1')
    sapg_stage1_std2 = fields.Char(string='Stage 1: Standard 2')
    sapg_stage1_planned = fields.Date(string='Stage 1: Planned Date')
    sapg_stage1_actual = fields.Date(string='Stage 1: Actual Date')
    sapg_stage2_employees = fields.Char(string='Stage 2: Number of Employees')
    sapg_stage2_risk = fields.Char(string='Stage 2: Risk / Complexity Rate')
    sapg_stage2_std1 = fields.Char(string='Stage 2: Standard 1')
    sapg_stage2_std2 = fields.Char(string='Stage 2: Standard 2')
    sapg_stage2_planned = fields.Date(string='Stage 2: Planned Date (PT)')
    sapg_stage2_actual = fields.Date(string='Stage 2: Actual Date (GT)')
    sapg_surv1_employees = fields.Char(string='1. Surveillance: Number of Employees')
    sapg_surv1_risk = fields.Char(string='1. Surveillance: Risk / Complexity Rate')
    sapg_surv1_std1 = fields.Char(string='1. Surveillance: Standard 1')
    sapg_surv1_std2 = fields.Char(string='1. Surveillance: Standard 2')
    sapg_surv1_planned = fields.Date(string='1. Surveillance: Planned Date (PT)')
    sapg_surv1_actual = fields.Date(string='1. Surveillance: Actual Date (GT)')
    sapg_surv2_employees = fields.Char(string='2. Surveillance: Number of Employees')
    sapg_surv2_risk = fields.Char(string='2. Surveillance: Risk / Complexity Rate')
    sapg_surv2_std1 = fields.Char(string='2. Surveillance: Standard 1')
    sapg_surv2_std2 = fields.Char(string='2. Surveillance: Standard 2')
    sapg_surv2_planned = fields.Date(string='2. Surveillance: Planned Date (PT)')
    sapg_surv2_actual = fields.Date(string='2. Surveillance: Actual Date (GT)')
    sapg_recert_employees = fields.Char(string='Recertification: Number of Employees')
    sapg_recert_risk = fields.Char(string='Recertification: Risk / Complexity Rate')
    sapg_recert_std1 = fields.Char(string='Recertification: Standard 1')
    sapg_recert_std2 = fields.Char(string='Recertification: Standard 2')
    sapg_recert_planned = fields.Date(string='Recertification: Planned Date (PT)')
    sapg_recert_actual = fields.Date(string='Recertification: Actual Date (GT)')
    sapg_update_date = fields.Date(string='Date of Update')
    sapg_updated_by = fields.Char(string='Updated By')
    sapg_signature = fields.Binary(string='Signature', copy=False)

    # ------------------------------------------------------------------
    # PDF helpers
    # ------------------------------------------------------------------
    def _ect_standard_grid(self):
        """[[(label, ticked)] x 3, free text] for the two rows of the ESYD standards grid."""
        self.ensure_one()
        cells = [(label, self[fname]) for fname, label, _codes in ECT_STANDARDS]
        return [(cells[0:3], self.ect_std_other_1 or ''), (cells[3:6], self.ect_std_other_2 or '')]

    def _ect_head_rows(self):
        return _rows(self.ect_head_ids, 3)

    def _ect_site_rows(self):
        return _rows(self.ect_site_ids, 3)

    def _pct_head_rows(self):
        return _rows(self.pct_head_ids, 3)

    def _pct_site_rows(self):
        return _rows(self.pct_site_ids, 3)

    def _pcr_sections(self):
        """[(criteria label, rating)] of sections 1 and 2."""
        self.ensure_one()
        return ([(label, self[fname]) for fname, label in PCR_CONDUCT],
                [(label, self[fname]) for fname, label in PCR_EXECUTION])

    def _pcr_rating_columns(self):
        return PCR_RATINGS

    def _sapg_question_pages(self):
        """The questions split as in the Word form: "COMPANY PERFORMANCE DATA" starts a new page."""
        self.ensure_one()
        questions = self.sapg_question_ids
        for i, question in enumerate(questions):
            if question.is_section and (question.name or '').strip() == 'COMPANY PERFORMANCE DATA':
                return questions[:i], questions[i:]
        return questions, questions.browse()

    def _sapg_stages(self):
        """Per audit column: dict(key, title, employees, risk, std1, std2, planned, actual)."""
        self.ensure_one()
        return [{
            'key': key,
            'title': title,
            'employees': self['sapg_%s_employees' % key] or '',
            'risk': self['sapg_%s_risk' % key] or '',
            'std1': self['sapg_%s_std1' % key] or '',
            'std2': self['sapg_%s_std2' % key] or '',
            'planned': _fmt_date(self['sapg_%s_planned' % key]),
            'actual': _fmt_date(self['sapg_%s_actual' % key]),
        } for key, title in SAPG_STAGES]


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = ['tuv.audit.plan', 'tuv.acc.small.forms.mixin']

    ect_head_ids = fields.One2many('tuv.form.ect.address', 'plan_id', string='Address of Head Office',
                                   copy=True)
    ect_site_ids = fields.One2many('tuv.form.ect.address', 'site_plan_id',
                                   string='Address of Other Sites', copy=True)
    ect_ggap_line_ids = fields.One2many('tuv.form.ect.ggap.line', 'plan_id',
                                        string='GLOBALG.A.P. Special Requirements', copy=True)
    pct_head_ids = fields.One2many('tuv.form.pct.address', 'plan_id', string='Address of Head Office',
                                   copy=True)
    pct_site_ids = fields.One2many('tuv.form.pct.address', 'site_plan_id',
                                   string='Address of Other Sites', copy=True)
    sapg_item_ids = fields.One2many('tuv.form.sapg.item', 'plan_id', string='Items to be Examined',
                                    copy=True)
    sapg_question_ids = fields.One2many('tuv.form.sapg.question', 'plan_id',
                                        string='Changes / Company Performance Data', copy=True)

    def _tuv_fill_esyd_certificate_text(self):
        """Called from data: the GLOBALG.A.P. requirement rows of the Word form, once."""
        for plan in self:
            if not plan.ect_ggap_line_ids:
                plan.ect_ggap_line_ids = ect_ggap_commands()

    def _tuv_fill_saac_audit_program(self):
        """Called from data: the clause rows and the questions of the Word form, once."""
        for plan in self:
            if not plan.sapg_item_ids:
                plan.sapg_item_ids = sapg_item_commands()
            if not plan.sapg_question_ids:
                plan.sapg_question_ids = sapg_question_commands()


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'tuv.acc.small.forms.mixin']

    # ----- tables: the rows of the Word form, added once the form is picked -----
    ect_head_ids = fields.One2many(
        'tuv.form.ect.address', 'project_id', string='Address of Head Office',
        compute='_compute_ect_head_ids', store=True, readonly=False)
    ect_site_ids = fields.One2many(
        'tuv.form.ect.address', 'site_project_id', string='Address of Other Sites',
        compute='_compute_ect_site_ids', store=True, readonly=False)
    ect_ggap_line_ids = fields.One2many(
        'tuv.form.ect.ggap.line', 'project_id', string='GLOBALG.A.P. Special Requirements',
        compute='_compute_ect_ggap_line_ids', store=True, readonly=False)
    pct_head_ids = fields.One2many(
        'tuv.form.pct.address', 'project_id', string='Address of Head Office',
        compute='_compute_pct_head_ids', store=True, readonly=False)
    pct_site_ids = fields.One2many(
        'tuv.form.pct.address', 'site_project_id', string='Address of Other Sites',
        compute='_compute_pct_site_ids', store=True, readonly=False)
    sapg_item_ids = fields.One2many(
        'tuv.form.sapg.item', 'project_id', string='Items to be Examined',
        compute='_compute_sapg_item_ids', store=True, readonly=False)
    sapg_question_ids = fields.One2many(
        'tuv.form.sapg.question', 'project_id', string='Changes / Company Performance Data',
        compute='_compute_sapg_question_ids', store=True, readonly=False)

    # ----- filled from the project, still editable -----
    ect_std_iso9001 = fields.Boolean(compute='_compute_ect_standards', store=True, readonly=False)
    ect_std_iso22000 = fields.Boolean(compute='_compute_ect_standards', store=True, readonly=False)
    ect_std_iso27001 = fields.Boolean(compute='_compute_ect_standards', store=True, readonly=False)
    ect_std_iso14001 = fields.Boolean(compute='_compute_ect_standards', store=True, readonly=False)
    ect_std_iso45001 = fields.Boolean(compute='_compute_ect_standards', store=True, readonly=False)
    ect_std_iso20000 = fields.Boolean(compute='_compute_ect_standards', store=True, readonly=False)
    ect_std_other_1 = fields.Char(compute='_compute_ect_standards', store=True, readonly=False)
    ect_lead_auditor_id = fields.Many2one(compute='_compute_ct_contacts', store=True, readonly=False)
    ect_rep_phone = fields.Char(compute='_compute_ct_contacts', store=True, readonly=False)
    ect_rep_email = fields.Char(compute='_compute_ct_contacts', store=True, readonly=False)

    pct_std_iso9001 = fields.Boolean(compute='_compute_pct_standards', store=True, readonly=False)
    pct_std_iso22000 = fields.Boolean(compute='_compute_pct_standards', store=True, readonly=False)
    pct_std_iso14001 = fields.Boolean(compute='_compute_pct_standards', store=True, readonly=False)
    pct_std_iso45001 = fields.Boolean(compute='_compute_pct_standards', store=True, readonly=False)
    pct_std_others = fields.Boolean(compute='_compute_pct_standards', store=True, readonly=False)
    pct_std_others_text = fields.Char(compute='_compute_pct_standards', store=True, readonly=False)
    pct_lead_auditor_id = fields.Many2one(compute='_compute_ct_contacts', store=True, readonly=False)
    pct_rep_phone = fields.Char(compute='_compute_ct_contacts', store=True, readonly=False)
    pct_rep_email = fields.Char(compute='_compute_ct_contacts', store=True, readonly=False)

    pcr_client_name = fields.Char(compute='_compute_pcr_from_project', store=True, readonly=False)
    pcr_audit_dates = fields.Char(compute='_compute_pcr_from_project', store=True, readonly=False)
    pcr_auditor_name = fields.Char(compute='_compute_pcr_from_project', store=True, readonly=False)
    pcr_standard = fields.Char(compute='_compute_pcr_from_project', store=True, readonly=False)
    pcr_completed_by = fields.Char(compute='_compute_pcr_from_project', store=True, readonly=False)

    saa_auditor_id = fields.Many2one(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_assignment = fields.Char(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_client = fields.Char(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_standards = fields.Char(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_certificate_numbers = fields.Char(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_audit_type = fields.Char(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_possible_scope = fields.Text(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_location = fields.Text(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_audit = fields.Char(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_order = fields.Char(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_client_address = fields.Text(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_client_contact = fields.Char(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_client_contact_persons = fields.Char(compute='_compute_saa_from_project', store=True,
                                             readonly=False)
    saa_audit_scopes = fields.Text(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_personnel = fields.Char(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_audit_team = fields.Text(compute='_compute_saa_from_project', store=True, readonly=False)
    saa_duration = fields.Char(compute='_compute_saa_from_project', store=True, readonly=False)

    sapg_company_name = fields.Char(compute='_compute_sapg_from_project', store=True, readonly=False)
    sapg_addresses = fields.Text(compute='_compute_sapg_from_project', store=True, readonly=False)
    sapg_scope = fields.Text(compute='_compute_sapg_from_project', store=True, readonly=False)
    sapg_ea_nace = fields.Char(compute='_compute_sapg_from_project', store=True, readonly=False)
    sapg_category = fields.Char(compute='_compute_sapg_from_project', store=True, readonly=False)
    sapg_employees = fields.Char(compute='_compute_sapg_from_project', store=True, readonly=False)
    sapg_standards = fields.Char(compute='_compute_sapg_from_project', store=True, readonly=False)
    sapg_audit_responsible = fields.Char(compute='_compute_sapg_from_project', store=True,
                                         readonly=False)
    sapg_certificate = fields.Char(compute='_compute_sapg_from_project', store=True, readonly=False)
    sapg_stage1_std1 = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_stage1_std2 = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_stage2_std1 = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_stage2_std2 = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_surv1_std1 = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_surv1_std2 = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_surv2_std1 = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_surv2_std2 = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_recert_std1 = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_recert_std2 = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_stage1_employees = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_stage2_employees = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_surv1_employees = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_surv2_employees = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_recert_employees = fields.Char(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_stage1_planned = fields.Date(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_stage2_planned = fields.Date(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_surv1_planned = fields.Date(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_surv2_planned = fields.Date(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_recert_planned = fields.Date(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_stage1_actual = fields.Date(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_stage2_actual = fields.Date(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_surv1_actual = fields.Date(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_surv2_actual = fields.Date(compute='_compute_sapg_stages', store=True, readonly=False)
    sapg_recert_actual = fields.Date(compute='_compute_sapg_stages', store=True, readonly=False)

    # ----- tables -----
    @api.depends('audit_report_id')
    def _compute_ect_head_ids(self):
        for project in self:
            if not project.ect_head_ids and project.audit_report_key == 'esyd_certificate_text':
                project.ect_head_ids = _head_office_commands(project)
            else:
                project.ect_head_ids = project.ect_head_ids

    @api.depends('audit_report_id')
    def _compute_ect_site_ids(self):
        for project in self:
            if not project.ect_site_ids and project.audit_report_key == 'esyd_certificate_text':
                project.ect_site_ids = _site_commands(project)
            else:
                project.ect_site_ids = project.ect_site_ids

    @api.depends('audit_report_id')
    def _compute_ect_ggap_line_ids(self):
        for project in self:
            if not project.ect_ggap_line_ids and project.audit_report_key == 'esyd_certificate_text':
                project.ect_ggap_line_ids = ect_ggap_commands()
            else:
                project.ect_ggap_line_ids = project.ect_ggap_line_ids

    @api.depends('audit_report_id')
    def _compute_pct_head_ids(self):
        for project in self:
            if not project.pct_head_ids and project.audit_report_key == 'pnac_certificate_text':
                project.pct_head_ids = _head_office_commands(project)
            else:
                project.pct_head_ids = project.pct_head_ids

    @api.depends('audit_report_id')
    def _compute_pct_site_ids(self):
        for project in self:
            if not project.pct_site_ids and project.audit_report_key == 'pnac_certificate_text':
                project.pct_site_ids = _site_commands(project)
            else:
                project.pct_site_ids = project.pct_site_ids

    @api.depends('audit_report_id')
    def _compute_sapg_item_ids(self):
        for project in self:
            if not project.sapg_item_ids and project.audit_report_key == 'saac_audit_program':
                project.sapg_item_ids = sapg_item_commands()
            else:
                project.sapg_item_ids = project.sapg_item_ids

    @api.depends('audit_report_id')
    def _compute_sapg_question_ids(self):
        for project in self:
            if not project.sapg_question_ids and project.audit_report_key == 'saac_audit_program':
                project.sapg_question_ids = sapg_question_commands()
            else:
                project.sapg_question_ids = project.sapg_question_ids

    @api.depends('audit_report_id')
    def _compute_er_requirement_ids(self):
        # the PNAC technical expert report is the TUV expert report: same rows, own card
        super()._compute_er_requirement_ids()
        for project in self:
            if not project.er_requirement_ids and project.audit_report_key == 'pnac_expert_report':
                project.er_requirement_ids = expert_requirement_commands()

    # ----- certificate texts -----
    @api.depends('ap_standard_line_ids.standard')
    def _compute_ect_standards(self):
        labels = dict(STANDARDS)
        covered = {code for _f, _l, codes in ECT_STANDARDS for code in codes}
        for project in self:
            codes = project.ap_standard_line_ids.mapped('standard')
            for fname, _label, standard_codes in ECT_STANDARDS:
                project[fname] = bool(set(codes) & set(standard_codes))
            # a standard the grid has no box for goes into its first free cell
            project.ect_std_other_1 = ', '.join(labels[c] for c in codes if c and c not in covered) or False

    @api.depends('ap_standard_line_ids.standard')
    def _compute_pct_standards(self):
        labels = dict(STANDARDS)
        covered = {code for _f, _l, codes in PCT_STANDARDS for code in codes}
        for project in self:
            codes = project.ap_standard_line_ids.mapped('standard')
            for fname, _label, standard_codes in PCT_STANDARDS:
                project[fname] = bool(set(codes) & set(standard_codes))
            others = [labels[c] for c in codes if c and c not in covered]
            project.pct_std_others = bool(others)
            project.pct_std_others_text = ', '.join(others) or False

    @api.depends('ap_lead_auditor_id', 'ap_partner_id', 'ap_representative_email')
    def _compute_ct_contacts(self):
        for project in self:
            phone = project.ap_partner_id.phone or False
            email = project.ap_representative_email or project.ap_partner_id.email or False
            project.ect_lead_auditor_id = project.ap_lead_auditor_id
            project.pct_lead_auditor_id = project.ap_lead_auditor_id
            project.ect_rep_phone = project.pct_rep_phone = phone
            project.ect_rep_email = project.pct_rep_email = email

    # ----- client response form -----
    @api.depends('ap_partner_id', 'ap_audit_date_stage1', 'ap_audit_date_stage2', 'ap_audit_date_until',
                 'ap_lead_auditor_id', 'ap_auditor_names', 'ap_standards_display', 'ap_representative')
    def _compute_pcr_from_project(self):
        for project in self:
            project.pcr_client_name = project.ap_partner_id.name or False
            project.pcr_audit_dates = _audit_dates_text(project)
            names = [project.ap_lead_auditor_id.name] + (project.ap_auditor_names or '').split(', ')
            project.pcr_auditor_name = ' / '.join(dict.fromkeys(filter(None, names))) or False
            project.pcr_standard = project.ap_standards_display or False
            project.pcr_completed_by = project.ap_representative or False

    # ----- auditor assignment -----
    @api.depends('ap_partner_id', 'ap_company_address', 'ap_other_sites', 'ap_representative',
                 'ap_representative_email', 'ap_certificate_scope', 'ap_audit_date_stage1',
                 'ap_audit_date_stage2', 'ap_audit_date_until', 'ap_employee_count',
                 'ap_lead_auditor_id', 'ap_team_line_ids.partner_id', 'ap_team_line_ids.role',
                 'ap_standards_display', 'ap_standard_line_ids.audit_type', 'certificate_no',
                 'md_sale_order_id.scope_of_certification', 'md_sale_order_id.audit_site',
                 'md_audit_duration', 'ap_audit_duration_hours')
    def _compute_saa_from_project(self):
        type_labels = dict(AUDIT_TYPES)
        role_labels = dict(TEAM_ROLES)
        for project in self:
            order = project.md_sale_order_id
            client = project.ap_partner_id.name or ''
            audit_types = ', '.join(dict.fromkeys(
                type_labels[t] for t in project.ap_standard_line_ids.mapped('audit_type') if t))
            project.saa_auditor_id = project.ap_lead_auditor_id
            project.saa_client = client or False
            project.saa_standards = project.ap_standards_display or False
            project.saa_certificate_numbers = project.certificate_no or False
            project.saa_audit_type = audit_types or False
            project.saa_assignment = 'Audit Assignment_%s_%s_%s' % (
                client, project.ap_standards_display or '', audit_types) if client else False
            project.saa_possible_scope = order.scope_of_certification or False
            project.saa_location = (order.audit_site or ', '.join(_address_lines(project))
                                    + ('\n' + project.ap_other_sites if project.ap_other_sites else '')) or False
            project.saa_audit = _audit_dates_text(project)
            project.saa_order = order.name or False
            project.saa_client_address = '\n'.join(_address_lines(project)) or False
            project.saa_client_contact = ', '.join(filter(None, [
                project.ap_partner_id.phone,
                project.ap_representative_email or project.ap_partner_id.email])) or False
            project.saa_client_contact_persons = project.ap_representative or False
            project.saa_audit_scopes = project.ap_certificate_scope or False
            project.saa_personnel = str(project.ap_employee_count) if project.ap_employee_count else False
            team = []
            if project.ap_lead_auditor_id:
                team.append('%s (Lead Auditor)' % project.ap_lead_auditor_id.name)
            team += ['%s (%s)' % (line.partner_id.name, role_labels.get(line.role, ''))
                     for line in project.ap_team_line_ids if line.partner_id]
            project.saa_audit_team = '\n'.join(team) or False
            hours = project.ap_audit_duration_hours
            duration = project.md_audit_duration or ''
            if hours:
                duration += ' (%g h)' % hours
            project.saa_duration = duration.strip() or False

    # ----- audit program -----
    def _sapg_certificate(self):
        """The project's current certificate (the last one not cancelled)."""
        self.ensure_one()
        return self.certificate_ids.filtered(lambda c: c.state != 'cancelled').sorted('id')[-1:]

    @api.depends('ap_partner_id', 'ap_company_address', 'ap_other_sites', 'ap_certificate_scope',
                 'ea_code_ids', 'ap_nace_code', 'ap_category', 'ap_employee_count',
                 'ap_standards_display', 'ap_representative', 'certificate_no',
                 'certificate_ids.state', 'certificate_ids.certificate_number',
                 'certificate_ids.issue_date')
    def _compute_sapg_from_project(self):
        for project in self:
            certificate = project._sapg_certificate()
            project.sapg_company_name = project.ap_partner_id.name or False
            project.sapg_addresses = '\n'.join(filter(None, [
                ', '.join(_address_lines(project)), project.ap_other_sites])) or False
            project.sapg_scope = project.ap_certificate_scope or False
            project.sapg_ea_nace = ' / '.join(filter(None, [
                ', '.join(project.ea_code_ids.mapped('name')), project.ap_nace_code])) or False
            project.sapg_category = project.ap_category or False
            project.sapg_employees = str(project.ap_employee_count) if project.ap_employee_count else False
            project.sapg_standards = project.ap_standards_display or False
            project.sapg_audit_responsible = project.ap_representative or False
            number = certificate.certificate_number or project.certificate_no
            project.sapg_certificate = ' / '.join(filter(None, [
                number, _fmt_date(certificate.issue_date)])) or False

    @api.depends('ap_standard_line_ids.standard', 'ap_employee_count', 'md_audit_type',
                 'ap_audit_date_stage1', 'ap_audit_date_stage2', 'md_audit_date_surveillance',
                 'md_audit_date_recert', 'certificate_ids.state',
                 'certificate_ids.surveillance_1_date', 'certificate_ids.surveillance_2_date',
                 'certificate_ids.expiry_date')
    def _compute_sapg_stages(self):
        for project in self:
            labels = _standard_labels(project)
            certificate = project._sapg_certificate()
            current = SAPG_STAGE_BY_AUDIT.get(project.md_audit_type, ())
            employees = str(project.ap_employee_count) if project.ap_employee_count else False
            audit_day = project.ap_audit_date_stage2 or project.ap_audit_date_stage1
            planned = {
                'stage1': project.ap_audit_date_stage1,
                'stage2': project.ap_audit_date_stage2,
                'surv1': certificate.surveillance_1_date,
                'surv2': certificate.surveillance_2_date,
                # the recertification audit is due before the certificate expires
                'recert': certificate.expiry_date,
            }
            actual = {
                'stage1': project.ap_audit_date_stage1,
                'stage2': project.ap_audit_date_stage2,
                'surv1': project.md_audit_date_surveillance or audit_day,
                'surv2': project.md_audit_date_surveillance or audit_day,
                'recert': project.md_audit_date_recert or audit_day,
            }
            for key, _title in SAPG_STAGES:
                project['sapg_%s_std1' % key] = labels[0] if labels else False
                project['sapg_%s_std2' % key] = labels[1] if len(labels) > 1 else False
                project['sapg_%s_planned' % key] = planned[key] or False
                # what is known of the audit being done now goes into its own column only
                project['sapg_%s_employees' % key] = employees if key in current else False
                project['sapg_%s_actual' % key] = (actual[key] or False) if key in current else False
