import functools
import json

from odoo import Command, api, fields, models
from odoo.tools import file_open

AR_KEY = 'audit_report'
AR_SECTIONS = [
    ('stage1', 'Result of Audit Stage 1'),
    ('conclusions', 'Audit Conclusions'),
    ('iso27001', 'Annex A of ISO 27001:2022'),
    ('iso27701', 'Annex A and Annex B of ISO 27701:2019'),
    ('sikat', 'Critical Processes (IT-SiKat)'),
    ('iso20000', 'ISO 20000-1'),
    ('iso22301', 'ISO 22301'),
]
AR_ROW_KINDS = [
    ('head', 'Section'),
    ('sub', 'Sub-heading'),
    ('item', 'Requirement (audited + rating)'),
    ('comment', 'Conclusion / Comment'),
    ('text', 'Requirement (evidence text)'),
    ('location', 'Location (audited + remote)'),
    ('topic', 'Stage 1 topic'),
]
# *) RATING of audit findings, section 3 of the form
AR_RATINGS = [
    ('1', '1: Fully compliant'),
    ('2', '2: Opportunity for improvement'),
    ('3', '3: Minor nonconformity'),
    ('4', '4: Major nonconformity - documents'),
    ('5', '5: Major nonconformity - re-audit'),
    ('na', 'NA: Not applicable / excluded'),
]
AR_FINDING_KINDS = [
    ('deviation', 'Deviation of Stage 1'),
    ('positive', 'Positive Finding'),
    ('nc_last', 'Nonconformity from the Last Audit'),
    ('nc_this', 'Finding / Nonconformity from this Audit'),
]
NC_GRADE_RATING = {'minor_nc': '3', 'major_nc': '4'}
AUDIT_TYPE_SUGGESTION = {
    'initial': 'issue', 'pre_audit': 'issue',
    'surveillance_1': 'maintenance', 'surveillance_2': 'maintenance',
    'recertification': 'renewal',
}


@functools.lru_cache(maxsize=None)
def audit_report_data():
    """The fixed rows of form FM-TAGMBH-MSZ-003, taken from the Word form."""
    with file_open('tuv_audit_reports/data/checklists/audit_report.json') as f:
        return json.load(f)


def report_row_commands(section=None):
    return [Command.create(dict(row, sequence=index))
            for index, row in enumerate(audit_report_data()['rows'])
            if section is None or row['section'] == section]


class AuditReportRow(models.Model):
    """A row of one of the tables of the audit report (stage 1 result, audit conclusions,
    inspected requirements). Its kind decides which inputs it has."""

    _name = 'tuv.form.report.row'
    _description = 'Audit Report Row'
    _order = 'section, sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    sequence = fields.Integer(readonly=True)
    section = fields.Selection(AR_SECTIONS, required=True, readonly=True, index=True)
    kind = fields.Selection(AR_ROW_KINDS, required=True, readonly=True)
    label = fields.Text(string='Requirement', readonly=True)
    audited = fields.Boolean(string='Audited')
    remote = fields.Boolean(string='Remote')
    rating = fields.Selection(AR_RATINGS, string='Rating')
    comment = fields.Text(string='Conclusion / Comment / Evidence')
    ca = fields.Boolean(string='CA / R')
    sa1 = fields.Boolean(string='1. SA')
    sa2 = fields.Boolean(string='2. SA')
    std1 = fields.Text(string='Standard 1')
    std2 = fields.Text(string='Standard 2')
    std3 = fields.Text(string='Standard 3')
    std4 = fields.Text(string='Standard 4')
    std5 = fields.Text(string='Standard 5')


class AuditReportFinding(models.Model):
    """A line of the deviation, positive finding and finding / nonconformity lists."""

    _name = 'tuv.form.report.finding'
    _description = 'Audit Report Finding'
    _order = 'kind, sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    kind = fields.Selection(AR_FINDING_KINDS, required=True, index=True)
    sequence = fields.Integer(default=10)
    number = fields.Char(string='No.')
    standard = fields.Char(string='Relevant Standard')
    clause = fields.Char(string='Clause of the Standard')
    description = fields.Text(string='Description of Finding')
    rating = fields.Selection(AR_RATINGS, string='Rating')
    corrective_action = fields.Text(string='Root Cause and Corrective Action')
    completion_date = fields.Date(string='Completion of Corrective Action Until')
    evidence = fields.Text(string='Correction Evidence')
    verification = fields.Text(string='Evaluation / Verification of Corrective Action')
    nonconformity_id = fields.Many2one('tuv.audit.nonconformity', string='Nonconformity',
                                       ondelete='set null')


def _finding_field(inverse, kind, string, **kwargs):
    return fields.One2many('tuv.form.report.finding', inverse, string=string,
                           domain=[('kind', '=', kind)], context={'default_kind': kind}, **kwargs)


def _row_field(inverse, section, string, **kwargs):
    return fields.One2many('tuv.form.report.row', inverse, string=string,
                           domain=[('section', '=', section)], **kwargs)


class AuditReportFormMixin(models.AbstractModel):
    """Audit report, form FM-TAGMBH-MSZ-003, past its sections 1 and 2."""

    _name = 'tuv.audit.report.form.mixin'
    _description = 'Audit Report Fields'

    ar_stage1_result = fields.Text(string='Result of Audit Stage 1',
                                   help='Statement on the summary result of stage 1.')
    ar_dev_place_date = fields.Char(string='Deviations: Place, Date')
    ar_dev_completion_place_date = fields.Char(string='Deviations Completed: Place, Date')
    ar_nc_place_date = fields.Char(string='Findings: Place, Date')
    ar_nc_completion_place_date = fields.Char(string='Corrective Action Completed: Place, Date')
    ar_scope_appropriate = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                            string='The Certification Scope is Appropriate')
    ar_objectives_fulfilled = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                               string='The Audit Objectives have been Fulfilled')
    ar_rec_standards = fields.Char(string='Standard(s)')
    ar_rec_suggestion = fields.Selection([
        ('issue', 'Issue of the certificate'),
        ('maintenance', 'Maintenance of certificate'),
        ('renewal', 'Renewal of certificate'),
        ('withdrawal', 'Withdrawal of certificate'),
    ], string='Audit Team Suggestion')
    ar_rec_after = fields.Selection([
        ('no_action', 'no other action'),
        ('documents', 'Correction of nonconformities with the submission of documents'),
        ('reaudit', 'Correction of nonconformities with the Re-audit'),
    ], string='After')
    ar_place = fields.Char(string='Place')
    ar_date = fields.Date(string='Date')
    ar_lead_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    ar_auditor_signature = fields.Binary(string='Auditor(s) Signature', copy=False)

    def _ar_rows(self, section):
        return self.ar_row_ids.filtered(lambda r: r.section == section).sorted('sequence')


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = ['tuv.audit.plan', 'tuv.audit.report.form.mixin']

    ar_row_ids = fields.One2many('tuv.form.report.row', 'plan_id', string='Report Rows')
    ar_stage1_row_ids = _row_field('plan_id', 'stage1', 'Result of Audit Stage 1')
    ar_conclusion_row_ids = _row_field('plan_id', 'conclusions', 'Audit Conclusions')
    ar_iso27001_row_ids = _row_field('plan_id', 'iso27001', 'Annex A of ISO 27001:2022')
    ar_iso27701_row_ids = _row_field('plan_id', 'iso27701', 'Annex A and B of ISO 27701:2019')
    ar_sikat_row_ids = _row_field('plan_id', 'sikat', 'Critical Processes (IT-SiKat)')
    ar_iso20000_row_ids = _row_field('plan_id', 'iso20000', 'ISO 20000-1')
    ar_iso22301_row_ids = _row_field('plan_id', 'iso22301', 'ISO 22301')
    ar_deviation_ids = _finding_field('plan_id', 'deviation', 'List of Deviations for Stage 1')
    ar_positive_ids = _finding_field('plan_id', 'positive', 'List of Positive Findings')
    ar_nc_last_ids = _finding_field('plan_id', 'nc_last', 'Nonconformities from the Last Audit')
    ar_nc_this_ids = _finding_field('plan_id', 'nc_this', 'Findings / Nonconformities from this Audit')

    def _tuv_fill_report_rows(self):
        """Called from data: the fixed rows of the Word form, once."""
        for plan in self:
            if not plan.ar_row_ids:
                plan.ar_row_ids = report_row_commands()


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'tuv.audit.report.form.mixin']

    ar_row_ids = fields.One2many('tuv.form.report.row', 'project_id', string='Report Rows')
    # one field per table, each filled with its rows of the Word form once the report is picked
    ar_stage1_row_ids = _row_field('project_id', 'stage1', 'Result of Audit Stage 1',
                                   compute='_compute_ar_section_rows', store=True, readonly=False)
    ar_conclusion_row_ids = _row_field('project_id', 'conclusions', 'Audit Conclusions',
                                       compute='_compute_ar_section_rows', store=True, readonly=False)
    ar_iso27001_row_ids = _row_field('project_id', 'iso27001', 'Annex A of ISO 27001:2022',
                                     compute='_compute_ar_section_rows', store=True, readonly=False)
    ar_iso27701_row_ids = _row_field('project_id', 'iso27701', 'Annex A and B of ISO 27701:2019',
                                     compute='_compute_ar_section_rows', store=True, readonly=False)
    ar_sikat_row_ids = _row_field('project_id', 'sikat', 'Critical Processes (IT-SiKat)',
                                  compute='_compute_ar_section_rows', store=True, readonly=False)
    ar_iso20000_row_ids = _row_field('project_id', 'iso20000', 'ISO 20000-1',
                                     compute='_compute_ar_section_rows', store=True, readonly=False)
    ar_iso22301_row_ids = _row_field('project_id', 'iso22301', 'ISO 22301',
                                     compute='_compute_ar_section_rows', store=True, readonly=False)
    ar_deviation_ids = _finding_field('project_id', 'deviation', 'List of Deviations for Stage 1')
    ar_positive_ids = _finding_field('project_id', 'positive', 'List of Positive Findings')
    ar_nc_last_ids = _finding_field('project_id', 'nc_last', 'Nonconformities from the Last Audit')
    ar_nc_this_ids = _finding_field('project_id', 'nc_this', 'Findings / Nonconformities from this Audit',
                                    compute='_compute_ar_nc_this_ids', store=True, readonly=False)

    # filled from the project, still editable
    ar_rec_standards = fields.Char(compute='_compute_ar_recommendation', store=True, readonly=False)
    ar_rec_suggestion = fields.Selection(compute='_compute_ar_recommendation', store=True, readonly=False)
    ar_rec_after = fields.Selection(compute='_compute_ar_recommendation', store=True, readonly=False)
    ar_objectives_fulfilled = fields.Selection(compute='_compute_ar_recommendation', store=True,
                                               readonly=False)

    @api.depends('audit_report_id')
    def _compute_ar_section_rows(self):
        # the fixed rows of the Word form, added once the audit report is picked; entries are kept
        section_fields = {
            'stage1': 'ar_stage1_row_ids', 'conclusions': 'ar_conclusion_row_ids',
            'iso27001': 'ar_iso27001_row_ids', 'iso27701': 'ar_iso27701_row_ids',
            'sikat': 'ar_sikat_row_ids', 'iso20000': 'ar_iso20000_row_ids',
            'iso22301': 'ar_iso22301_row_ids',
        }
        for project in self:
            for section, fname in section_fields.items():
                if project.audit_report_key == AR_KEY and not project[fname]:
                    project[fname] = report_row_commands(section)
                else:
                    project[fname] = project[fname]

    @api.depends('nonconformity_ids.grade', 'nonconformity_ids.clause',
                 'nonconformity_ids.description', 'nonconformity_ids.root_cause',
                 'nonconformity_ids.corrective_action', 'nonconformity_ids.deadline',
                 'nonconformity_ids.client_evidence_name', 'nonconformity_ids.closure_note',
                 'nonconformity_ids.state')
    def _compute_ar_nc_this_ids(self):
        # the nonconformities raised at this audit (NC register, task 3.4)
        for project in self:
            ncs = project.nonconformity_ids.filtered(lambda nc: nc.state != 'cancelled')
            lines = [Command.clear()]
            for seq, nc in enumerate(ncs.sorted('id'), start=1):
                action = '\n'.join(filter(None, [nc.root_cause, nc.correction, nc.corrective_action]))
                lines.append(Command.create({
                    'kind': 'nc_this',
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
            project.ar_nc_this_ids = lines

    @api.depends('ap_standards_display', 'ap_standard_line_ids.audit_type',
                 'nonconformity_ids.grade', 'nonconformity_ids.state', 'report_conclusion')
    def _compute_ar_recommendation(self):
        for project in self:
            types = project.ap_standard_line_ids.mapped('audit_type')
            ncs = project.nonconformity_ids.filtered(lambda nc: nc.state != 'cancelled')
            project.ar_rec_standards = project.ap_standards_display
            project.ar_rec_suggestion = next(
                (AUDIT_TYPE_SUGGESTION[t] for t in types if t in AUDIT_TYPE_SUGGESTION), False)
            project.ar_rec_after = 'documents' if ncs else 'no_action'
            project.ar_objectives_fulfilled = {'recommend': 'yes', 'not_recommend': 'no'}.get(
                project.report_conclusion, False)
