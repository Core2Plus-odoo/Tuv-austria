import functools
import json

from odoo import Command, api, fields, models
from odoo.tools import file_open

# The audit reports of the accreditation bodies ESYD (FM-BA-ZET-MS-All-008-AR),
# PNAC (TUV/BA/FM/04-4) and SAAC (FM-BA-ZET-MS-All-010a-AR). They share their line models;
# `form` tells the three apart.
ACC_FORMS = [('esyd', 'ESYD'), ('pnac', 'PNAC'), ('saac', 'SAAC')]
ACC_KEYS = {'esyd': 'esyd_audit_report', 'pnac': 'pnac_audit_report', 'saac': 'saac_audit_report'}
ACC_SECTIONS = [
    ('stage1', 'Result of Audit Stage 1'),
    ('conclusions', 'Audit Conclusions'),
    ('isms', 'Information Security (ISO 27001)'),
    ('iso27001_2013', 'Annex A of ISO 27001:2013'),
    ('iso27001', 'Annex A of ISO 27001:2022'),
    ('iso27701', 'Annex A and Annex B of ISO 27701:2019'),
    ('sikat', 'Critical Processes (IT-SiKat)'),
    ('iso20000', 'ISO 20000-1'),
    ('iso22301', 'ISO 22301'),
]
ACC_ROW_KINDS = [
    ('head', 'Section'),
    ('sub', 'Sub-heading'),
    ('item', 'Requirement (audited + rating)'),
    ('comment', 'Conclusion / Comment'),
    ('text', 'Requirement (evidence text)'),
    ('location', 'Location (audited)'),
    ('topic', 'Stage 1 topic'),
    ('blank', 'Empty row'),
]
# rating / characterization of findings; PNAC only uses 1-4 (its 4 is the re-audit)
ACC_RATINGS = [
    ('1', '1: Fully compliant'),
    ('2', '2: Opportunity for improvement'),
    ('3', '3: Minor nonconformity'),
    ('4', '4: Major nonconformity'),
    ('5', '5: Major nonconformity - re-audit'),
    ('na', 'NA: Not applicable / excluded'),
]
ACC_FINDING_KINDS = [
    ('deviation', 'Deviation of Stage 1'),
    ('positive', 'Positive Finding'),
    ('finding', 'Finding / Nonconformity'),
]
YES_NO = [('yes', 'Yes'), ('no', 'No')]
NC_GRADE_RATING = {'minor_nc': '3', 'major_nc': '4'}
AUDIT_TYPE_SUGGESTION = {
    'initial': 'issue', 'pre_audit': 'issue',
    'surveillance_1': 'maintenance', 'surveillance_2': 'maintenance',
    'recertification': 'renewal',
}
# ESYD: "Audit: Stage 2 / Surveillance / Recertification" above the audit conclusions
AUDIT_TYPE_STAGE = {
    'initial': 'stage2',
    'surveillance_1': 'surveillance', 'surveillance_2': 'surveillance',
    'recertification': 'recertification',
}
SUGGESTIONS = [
    ('issue', 'Issue of the certificate'),
    ('maintenance', 'Maintenance of certificate'),
    ('renewal', 'Renewal of certificate'),
    ('withdrawal', 'Withdrawal of certificate'),
]
AFTER = [
    ('no_action', 'no other action'),
    ('documents', 'Correction of nonconformities with the submission of documents'),
    ('reaudit', 'Correction of nonconformities with the Re-audit'),
]

# project field of each table of the Word forms, per form
ROW_FIELDS = {
    'esyd': {'stage1': 'ear_stage1_row_ids', 'conclusions': 'ear_conclusion_row_ids'},
    'pnac': {'stage1': 'par_stage1_row_ids', 'conclusions': 'par_conclusion_row_ids'},
    'saac': {
        'stage1': 'sar_stage1_row_ids', 'conclusions': 'sar_conclusion_row_ids',
        'isms': 'sar_isms_row_ids', 'iso27001_2013': 'sar_iso27001_2013_row_ids',
        'iso27001': 'sar_iso27001_row_ids', 'iso27701': 'sar_iso27701_row_ids',
        'sikat': 'sar_sikat_row_ids', 'iso20000': 'sar_iso20000_row_ids',
        'iso22301': 'sar_iso22301_row_ids',
    },
}
FINDING_FIELDS = {'esyd': 'ear_finding_ids', 'pnac': 'par_finding_ids', 'saac': 'sar_finding_ids'}


@functools.lru_cache(maxsize=None)
def acc_report_data(form):
    """The fixed rows of the Word form (data/checklists/acc_reports_<form>.json)."""
    with file_open('tuv_audit_reports/data/checklists/acc_reports_%s.json' % form) as f:
        return json.load(f)


def acc_row_commands(form, section=None):
    return [Command.create(dict(row, form=form, sequence=index))
            for index, row in enumerate(acc_report_data(form)['rows'])
            if section is None or row['section'] == section]


class AccReportRow(models.Model):
    """A row of a table of the ESYD / PNAC / SAAC audit report (stage 1 result, audit
    conclusions, inspected requirements). Its kind decides which inputs it has."""

    _name = 'tuv.form.acc.report.row'
    _description = 'Accreditation Audit Report Row'
    _order = 'form, section, sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    form = fields.Selection(ACC_FORMS, required=True, readonly=True, index=True)
    sequence = fields.Integer(readonly=True)
    section = fields.Selection(ACC_SECTIONS, required=True, readonly=True, index=True)
    kind = fields.Selection(ACC_ROW_KINDS, required=True, readonly=True)
    label = fields.Text(string='Requirement', readonly=True)
    dark = fields.Boolean(readonly=True, help='Dark grey row in the Word form.')
    replace_label = fields.Boolean(
        readonly=True, help='The text is a template (version XX, A.xx): the entry replaces it.')
    audited = fields.Boolean(string='Audited')
    rating = fields.Selection(ACC_RATINGS, string='Rating')
    comment = fields.Text(string='Conclusion / Comment / Evidence')
    ca = fields.Boolean(string='CA / R')
    sa1 = fields.Boolean(string='1. SA')
    sa2 = fields.Boolean(string='2. SA')
    std1 = fields.Text(string='Standard 1')
    std2 = fields.Text(string='Standard 2')
    std3 = fields.Text(string='Standard 3')
    std4 = fields.Text(string='Standard 4')
    std5 = fields.Text(string='Standard 5')


class AccReportFinding(models.Model):
    """A line of the deviation, positive finding and finding / nonconformity lists."""

    _name = 'tuv.form.acc.report.finding'
    _description = 'Accreditation Audit Report Finding'
    _order = 'form, kind, sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    form = fields.Selection(ACC_FORMS, required=True, index=True)
    kind = fields.Selection(ACC_FINDING_KINDS, required=True, index=True)
    sequence = fields.Integer(default=10)
    number = fields.Char(string='No.')
    standard = fields.Char(string='Relevant Standard')
    clause = fields.Char(string='Clause of the Standard')
    description = fields.Text(string='Description of Finding')
    rating = fields.Selection(ACC_RATINGS, string='Rating')
    corrective_action = fields.Text(string='Root Cause and Corrective Action')
    completion_date = fields.Date(string='Completion of Corrective Action Until')
    evidence = fields.Text(string='Correction Evidence')
    verification = fields.Text(string='Evaluation / Verification of Corrective Action')
    nonconformity_id = fields.Many2one('tuv.audit.nonconformity', string='Nonconformity',
                                       ondelete='set null')


def _rows(inverse, form, section, string, **kwargs):
    return fields.One2many('tuv.form.acc.report.row', inverse, string=string,
                           domain=[('form', '=', form), ('section', '=', section)],
                           context={'default_form': form, 'default_section': section}, **kwargs)


def _findings(inverse, form, kind, string, **kwargs):
    return fields.One2many('tuv.form.acc.report.finding', inverse, string=string,
                           domain=[('form', '=', form), ('kind', '=', kind)],
                           context={'default_form': form, 'default_kind': kind}, **kwargs)


class EsydAuditReportMixin(models.AbstractModel):
    """ESYD audit report, form FM-BA-ZET-MS-All-008-AR-EN (revision 02_15.02.2024)."""

    _name = 'tuv.acc.esyd.report.mixin'
    _description = 'ESYD Audit Report Fields'

    ear_company_description = fields.Text(string='Company Description, Business Activities')
    ear_remote_activities = fields.Char(string='Use of Remote Activities (describe)')
    ear_stage1_result = fields.Text(string='Result of Audit Stage 1',
                                    help='Statement on the summary result of stage 1.')
    ear_dev_place_date = fields.Char(string='Deviations: Place, Date')
    ear_dev_rep_place_date = fields.Char(string='Completion (Company Representative): Place, Date')
    ear_dev_lead_place_date = fields.Char(string='Completion (Lead Auditor): Place, Date')
    ear_audit_stage = fields.Selection([
        ('stage2', 'Stage 2'),
        ('surveillance', 'Surveillance'),
        ('recertification', 'Recertification'),
    ], string='Audit')
    ear_scope_appropriate = fields.Selection(YES_NO, string='The Certification Scope is Appropriate')
    ear_objectives_fulfilled = fields.Selection(YES_NO, string='The Audit Objectives have been Fulfilled')
    ear_findings_raised = fields.Selection(YES_NO, string='Findings Raised',
                                           help='Yes: see Annex I. No: no annex required.')
    ear_rec_standards = fields.Char(string='Standard(s)')
    ear_rec_suggestion = fields.Selection([
        ('issue', 'Issue of the certificate / Verification Statement'),
        ('maintenance', 'Maintenance of Certificate'),
        ('renewal', 'Renewal of Certificate'),
        ('withdrawal', 'Withdrawal/ Suspension of Certificate'),
    ], string='Audit Team Suggestion')
    ear_rec_after = fields.Selection([
        ('no_action', 'No other action'),
        ('plan', 'Review and acceptance of the client’s plan for correction and corrective action'),
        ('documents', 'Correction of Non-Conformities with the submission of Documents'),
        ('reaudit', 'Correction of Non-Conformities with the Re-audit'),
    ], string='After')
    ear_place_date = fields.Char(string='Place, Date')
    ear_lead_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    ear_auditor_signature = fields.Binary(string='Auditor(s) Signature', copy=False)
    ear_client_name = fields.Char(string='Company Representative (Name and Surname)')
    ear_client_signature = fields.Binary(string='Signature / Stamp', copy=False)
    ear_next_audit = fields.Char(string='Period of the Next Audit (Month and Year)')
    ear_nc_place_date = fields.Char(string='Findings: Place, Date')
    ear_nc_rep_place_date = fields.Char(string='Completion (Company Representative): Place, Date')
    ear_nc_lead_place_date = fields.Char(string='Completion (Lead Auditor): Place, Date')

    def _ear_annex2(self):
        """Annex II of the form: pairs of cells, each a title line and its bullet lines."""
        return [[[line.lstrip('• ') for line in cell.split('\n')] for cell in row]
                for row in acc_report_data('esyd').get('annex2', [])]


class PnacAuditReportMixin(models.AbstractModel):
    """PNAC audit report, form TUV/BA/FM/04-4 (Rev 00, Issue 01, 31/07/2025)."""

    _name = 'tuv.acc.pnac.report.mixin'
    _description = 'PNAC Audit Report Fields'

    par_complexity = fields.Char(string='Complexity')
    par_stage1_result = fields.Text(string='Result of Audit Stage 1',
                                    help='Statement on the summary result of stage 1.')
    par_dev_place_date = fields.Char(string='Deviations: Place, Date')
    par_dev_rep_place_date = fields.Char(string='Completion (Company Representative): Place, Date')
    par_dev_lead_place_date = fields.Char(string='Completion (Lead Auditor): Place, Date')
    par_nc_place_date = fields.Char(string='Findings: Place, Date')
    par_nc_rep_place_date = fields.Char(string='Completion (Company Representative): Place, Date')
    par_nc_lead_place_date = fields.Char(string='Completion (Lead Auditor): Place, Date')
    par_scope_appropriate = fields.Selection(YES_NO, string='The Certification Scope is Appropriate')
    par_objectives_fulfilled = fields.Selection(YES_NO, string='The Audit Objectives have been Fulfilled')
    par_rec_standards = fields.Char(string='Standard(s)')
    par_rec_suggestion = fields.Selection(SUGGESTIONS, string='Audit Team Suggestion')
    par_rec_after = fields.Selection(AFTER, string='After')
    par_place_date = fields.Char(string='Place, Date')
    par_lead_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    par_auditor_signature = fields.Binary(string='Auditor(s) Signature', copy=False)
    par_client_name = fields.Char(string='Company Representative (Name)')
    par_client_signature = fields.Binary(string='Signature / Stamp', copy=False)
    par_next_audit = fields.Char(string='Period of the Next Audit (Month and Year)')


class SaacAuditReportMixin(models.AbstractModel):
    """SAAC audit report IMS, form FM-BA-ZET-MS-All-010a-AR (revision 08/30.07.2024)."""

    _name = 'tuv.acc.saac.report.mixin'
    _description = 'SAAC Audit Report Fields'

    sar_stage1_result = fields.Text(string='Result of Audit Stage 1',
                                    help='Statement on the summary result of stage 1.')
    sar_dev_place_date = fields.Char(string='Deviations: Place, Date')
    sar_dev_rep_place_date = fields.Char(string='Completion (Company Representative): Place, Date')
    sar_dev_lead_place_date = fields.Char(string='Completion (Lead Auditor): Place, Date')
    sar_nc_place_date = fields.Char(string='Findings: Place, Date')
    sar_nc_rep_place_date = fields.Char(string='Completion (Company Representative): Place, Date')
    sar_nc_lead_place_date = fields.Char(string='Completion (Lead Auditor): Place, Date')
    sar_scope_appropriate = fields.Selection(YES_NO, string='The Certification Scope is Appropriate')
    sar_objectives_fulfilled = fields.Selection(YES_NO, string='The Audit Objectives have been Fulfilled')
    sar_rec_standards = fields.Char(string='Standard(s)')
    sar_rec_suggestion = fields.Selection(SUGGESTIONS, string='Audit Team Suggestion')
    sar_rec_after = fields.Selection(AFTER, string='After')
    sar_place_date = fields.Char(string='Place, Date')
    sar_lead_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    sar_auditor_signature = fields.Binary(string='Auditor(s) Signature', copy=False)


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = ['tuv.audit.plan', 'tuv.acc.esyd.report.mixin', 'tuv.acc.pnac.report.mixin',
                'tuv.acc.saac.report.mixin']

    acc_row_ids = fields.One2many('tuv.form.acc.report.row', 'plan_id', string='Report Rows')

    ear_stage1_row_ids = _rows('plan_id', 'esyd', 'stage1', 'Result of Audit Stage 1')
    ear_conclusion_row_ids = _rows('plan_id', 'esyd', 'conclusions', 'Audit Conclusions')
    ear_deviation_ids = _findings('plan_id', 'esyd', 'deviation', 'List of Deviations for Stage 1')
    ear_finding_ids = _findings('plan_id', 'esyd', 'finding', 'Annex I: List of Findings')

    par_stage1_row_ids = _rows('plan_id', 'pnac', 'stage1', 'Result of Audit Stage 1')
    par_conclusion_row_ids = _rows('plan_id', 'pnac', 'conclusions', 'Audit Conclusions')
    par_deviation_ids = _findings('plan_id', 'pnac', 'deviation', 'List of Deviations for Stage 1')
    par_positive_ids = _findings('plan_id', 'pnac', 'positive', 'List of Positive Findings')
    par_finding_ids = _findings('plan_id', 'pnac', 'finding', 'List of Findings / Nonconformities')

    sar_stage1_row_ids = _rows('plan_id', 'saac', 'stage1', 'Result of Audit Stage 1')
    sar_conclusion_row_ids = _rows('plan_id', 'saac', 'conclusions', 'Audit Conclusions')
    sar_isms_row_ids = _rows('plan_id', 'saac', 'isms', 'Information Security (ISO 27001)')
    sar_iso27001_2013_row_ids = _rows('plan_id', 'saac', 'iso27001_2013', 'Annex A of ISO 27001:2013')
    sar_iso27001_row_ids = _rows('plan_id', 'saac', 'iso27001', 'Annex A of ISO 27001:2022')
    sar_iso27701_row_ids = _rows('plan_id', 'saac', 'iso27701', 'Annex A and B of ISO 27701:2019')
    sar_sikat_row_ids = _rows('plan_id', 'saac', 'sikat', 'Critical Processes (IT-SiKat)')
    sar_iso20000_row_ids = _rows('plan_id', 'saac', 'iso20000', 'ISO 20000-1')
    sar_iso22301_row_ids = _rows('plan_id', 'saac', 'iso22301', 'ISO 22301')
    sar_deviation_ids = _findings('plan_id', 'saac', 'deviation', 'List of Deviations for Stage 1')
    sar_positive_ids = _findings('plan_id', 'saac', 'positive', 'List of Positive Findings')
    sar_finding_ids = _findings('plan_id', 'saac', 'finding', 'List of Findings / Nonconformities')

    def _tuv_fill_acc_report_rows(self, form):
        """Called from data: the fixed rows of the Word form of `form`, once."""
        for plan in self:
            if not plan.acc_row_ids.filtered(lambda r: r.form == form):
                plan.acc_row_ids = acc_row_commands(form)


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'tuv.acc.esyd.report.mixin', 'tuv.acc.pnac.report.mixin',
                'tuv.acc.saac.report.mixin']

    # one field per table, each filled with its rows of the Word form once the report is picked
    ear_stage1_row_ids = _rows('project_id', 'esyd', 'stage1', 'Result of Audit Stage 1',
                               compute='_compute_acc_rows', store=True, readonly=False)
    ear_conclusion_row_ids = _rows('project_id', 'esyd', 'conclusions', 'Audit Conclusions',
                                   compute='_compute_acc_rows', store=True, readonly=False)
    ear_deviation_ids = _findings('project_id', 'esyd', 'deviation', 'List of Deviations for Stage 1')
    ear_finding_ids = _findings('project_id', 'esyd', 'finding', 'Annex I: List of Findings',
                                compute='_compute_acc_findings', store=True, readonly=False)

    par_stage1_row_ids = _rows('project_id', 'pnac', 'stage1', 'Result of Audit Stage 1',
                               compute='_compute_acc_rows', store=True, readonly=False)
    par_conclusion_row_ids = _rows('project_id', 'pnac', 'conclusions', 'Audit Conclusions',
                                   compute='_compute_acc_rows', store=True, readonly=False)
    par_deviation_ids = _findings('project_id', 'pnac', 'deviation', 'List of Deviations for Stage 1')
    par_positive_ids = _findings('project_id', 'pnac', 'positive', 'List of Positive Findings')
    par_finding_ids = _findings('project_id', 'pnac', 'finding', 'List of Findings / Nonconformities',
                                compute='_compute_acc_findings', store=True, readonly=False)

    sar_stage1_row_ids = _rows('project_id', 'saac', 'stage1', 'Result of Audit Stage 1',
                               compute='_compute_acc_rows', store=True, readonly=False)
    sar_conclusion_row_ids = _rows('project_id', 'saac', 'conclusions', 'Audit Conclusions',
                                   compute='_compute_acc_rows', store=True, readonly=False)
    sar_isms_row_ids = _rows('project_id', 'saac', 'isms', 'Information Security (ISO 27001)',
                             compute='_compute_acc_rows', store=True, readonly=False)
    sar_iso27001_2013_row_ids = _rows('project_id', 'saac', 'iso27001_2013', 'Annex A of ISO 27001:2013',
                                      compute='_compute_acc_rows', store=True, readonly=False)
    sar_iso27001_row_ids = _rows('project_id', 'saac', 'iso27001', 'Annex A of ISO 27001:2022',
                                 compute='_compute_acc_rows', store=True, readonly=False)
    sar_iso27701_row_ids = _rows('project_id', 'saac', 'iso27701', 'Annex A and B of ISO 27701:2019',
                                 compute='_compute_acc_rows', store=True, readonly=False)
    sar_sikat_row_ids = _rows('project_id', 'saac', 'sikat', 'Critical Processes (IT-SiKat)',
                              compute='_compute_acc_rows', store=True, readonly=False)
    sar_iso20000_row_ids = _rows('project_id', 'saac', 'iso20000', 'ISO 20000-1',
                                 compute='_compute_acc_rows', store=True, readonly=False)
    sar_iso22301_row_ids = _rows('project_id', 'saac', 'iso22301', 'ISO 22301',
                                 compute='_compute_acc_rows', store=True, readonly=False)
    sar_deviation_ids = _findings('project_id', 'saac', 'deviation', 'List of Deviations for Stage 1')
    sar_positive_ids = _findings('project_id', 'saac', 'positive', 'List of Positive Findings')
    sar_finding_ids = _findings('project_id', 'saac', 'finding', 'List of Findings / Nonconformities',
                                compute='_compute_acc_findings', store=True, readonly=False)

    # filled from the project, still editable
    ear_remote_activities = fields.Char(compute='_compute_acc_from_project', store=True, readonly=False)
    ear_client_name = fields.Char(compute='_compute_acc_from_project', store=True, readonly=False)
    ear_next_audit = fields.Char(compute='_compute_acc_from_project', store=True, readonly=False)
    par_complexity = fields.Char(compute='_compute_acc_from_project', store=True, readonly=False)
    par_client_name = fields.Char(compute='_compute_acc_from_project', store=True, readonly=False)
    par_next_audit = fields.Char(compute='_compute_acc_from_project', store=True, readonly=False)

    ear_audit_stage = fields.Selection(compute='_compute_acc_recommendation', store=True, readonly=False)
    ear_findings_raised = fields.Selection(compute='_compute_acc_recommendation', store=True,
                                           readonly=False)
    ear_rec_standards = fields.Char(compute='_compute_acc_recommendation', store=True, readonly=False)
    ear_rec_suggestion = fields.Selection(compute='_compute_acc_recommendation', store=True,
                                          readonly=False)
    ear_rec_after = fields.Selection(compute='_compute_acc_recommendation', store=True, readonly=False)
    ear_objectives_fulfilled = fields.Selection(compute='_compute_acc_recommendation', store=True,
                                                readonly=False)
    par_rec_standards = fields.Char(compute='_compute_acc_recommendation', store=True, readonly=False)
    par_rec_suggestion = fields.Selection(compute='_compute_acc_recommendation', store=True,
                                          readonly=False)
    par_rec_after = fields.Selection(compute='_compute_acc_recommendation', store=True, readonly=False)
    par_objectives_fulfilled = fields.Selection(compute='_compute_acc_recommendation', store=True,
                                                readonly=False)
    sar_rec_standards = fields.Char(compute='_compute_acc_recommendation', store=True, readonly=False)
    sar_rec_suggestion = fields.Selection(compute='_compute_acc_recommendation', store=True,
                                          readonly=False)
    sar_rec_after = fields.Selection(compute='_compute_acc_recommendation', store=True, readonly=False)
    sar_objectives_fulfilled = fields.Selection(compute='_compute_acc_recommendation', store=True,
                                                readonly=False)

    @api.depends('audit_report_id')
    def _compute_acc_rows(self):
        # the fixed rows of the Word form, added once its audit report is picked; entries are kept
        for project in self:
            for form, sections in ROW_FIELDS.items():
                for section, fname in sections.items():
                    if project.audit_report_key == ACC_KEYS[form] and not project[fname]:
                        project[fname] = acc_row_commands(form, section)
                    else:
                        project[fname] = project[fname]

    @api.depends('audit_report_id', 'nonconformity_ids.grade', 'nonconformity_ids.clause',
                 'nonconformity_ids.description', 'nonconformity_ids.root_cause',
                 'nonconformity_ids.correction', 'nonconformity_ids.corrective_action',
                 'nonconformity_ids.deadline', 'nonconformity_ids.client_evidence_name',
                 'nonconformity_ids.closure_note', 'nonconformity_ids.state')
    def _compute_acc_findings(self):
        # the nonconformities raised at this audit (NC register), only in the picked report:
        # the other reports keep their lines
        for project in self:
            for form, fname in FINDING_FIELDS.items():
                if project.audit_report_key != ACC_KEYS[form]:
                    project[fname] = project[fname]
                    continue
                ncs = project.nonconformity_ids.filtered(lambda nc: nc.state != 'cancelled')
                lines = [Command.clear()]
                for seq, nc in enumerate(ncs.sorted('id'), start=1):
                    action = '\n'.join(filter(None, [nc.root_cause, nc.correction, nc.corrective_action]))
                    lines.append(Command.create({
                        'form': form,
                        'kind': 'finding',
                        'sequence': seq,
                        'number': nc.name,
                        # the selection of `standard` is a method: ask the field for the label
                        'standard': nc._fields['standard'].convert_to_export(nc.standard, nc) or '',
                        'clause': nc.clause,
                        'description': nc.description,
                        'rating': NC_GRADE_RATING.get(nc.grade),
                        'corrective_action': action or False,
                        'completion_date': nc.deadline,
                        'evidence': nc.client_evidence_name,
                        'verification': nc.closure_note,
                        'nonconformity_id': nc.id,
                    }))
                project[fname] = lines

    @api.depends('ap_remote', 'ap_representative', 'md1_complexity_ranking',
                 'certificate_ids.next_surveillance_date')
    def _compute_acc_from_project(self):
        remote = dict(self._fields['ap_remote'].selection)
        for project in self:
            dates = [d for d in project.certificate_ids.mapped('next_surveillance_date') if d]
            next_audit = min(dates).strftime('%m/%Y') if dates else False
            project.ear_remote_activities = remote.get(project.ap_remote) or False
            project.ear_client_name = project.ap_representative
            project.ear_next_audit = next_audit
            project.par_complexity = project.md1_complexity_ranking
            project.par_client_name = project.ap_representative
            project.par_next_audit = next_audit

    @api.depends('ap_standards_display', 'ap_standard_line_ids.audit_type',
                 'nonconformity_ids.grade', 'nonconformity_ids.state', 'report_conclusion')
    def _compute_acc_recommendation(self):
        for project in self:
            types = project.ap_standard_line_ids.mapped('audit_type')
            ncs = project.nonconformity_ids.filtered(lambda nc: nc.state != 'cancelled')
            major = any(nc.grade == 'major_nc' for nc in ncs)
            suggestion = next((AUDIT_TYPE_SUGGESTION[t] for t in types if t in AUDIT_TYPE_SUGGESTION), False)
            fulfilled = {'recommend': 'yes', 'not_recommend': 'no'}.get(project.report_conclusion, False)
            for prefix in ('ear', 'par', 'sar'):
                project[prefix + '_rec_standards'] = project.ap_standards_display
                project[prefix + '_rec_suggestion'] = suggestion
                project[prefix + '_objectives_fulfilled'] = fulfilled
            project.ear_audit_stage = next((AUDIT_TYPE_STAGE[t] for t in types if t in AUDIT_TYPE_STAGE), False)
            project.ear_findings_raised = 'yes' if ncs else 'no'
            # what follows the audit, by the rating scale of each form: ESYD 3 = plan accepted,
            # 4 = documents; PNAC 3 = documents, 4 = re-audit; SAAC 3 = next audit, 4 = documents
            project.ear_rec_after = 'documents' if major else 'plan' if ncs else 'no_action'
            project.par_rec_after = 'reaudit' if major else 'documents' if ncs else 'no_action'
            project.sar_rec_after = 'documents' if major else 'no_action'
