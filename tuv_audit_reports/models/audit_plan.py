import base64

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import file_open

# The choices below are the drop-down lists of the Word form
# FM-TAGMBH-MSZ-001_Auditplan-EN (revision 08/22.01.2026).
AUDIT_METHODS = [
    ('single', 'Single audit'),
    ('combined', 'Combined audit'),
    ('integrated', 'Integrated audit'),
    ('multi_site', 'Multi site audit / Matrix audit'),
    ('others', 'Others'),
    ('self_definition', 'Self definition'),
]

STANDARDS = [
    ('iso_9001_2015', 'ISO 9001:2015'),
    ('iso_14001_2015', 'ISO 14001:2015'),
    ('iso_45001_2018', 'ISO 45001:2018'),
    ('iso_27001_2013', 'ISO 27001:2013'),
    ('iso_27001_2022', 'ISO 27001:2022'),
    ('iso_27018_2019', 'ISO 27018:2019'),
    ('iso_27019_2017', 'ISO 27019:2017'),
    ('iso_27701_2019', 'ISO 27701:2019'),
    ('it_sikat', 'IT-SiKat'),
    ('iso_20000_1_2018', 'ISO 20000-1:2018'),
    ('iso_50001_2018', 'ISO 50001:2018'),
    ('iso_22000_2018', 'ISO 22000:2018'),
    ('iso_13485_2016', 'ISO 13485:2016'),
    ('iso_21001_2018', 'ISO 21001:2018'),
    ('iso_29993_2017', 'ISO 29993:2017'),
    ('scc', 'SCC'),
    ('scp', 'SCP'),
    ('emas_iii', 'EMAS III'),
    ('iso_22301', 'ISO 22301'),
    ('iso_39001', 'ISO 39001'),
    ('globalgap', 'GLOBALGAP'),
    ('agro2', 'AGRO2'),
    ('fssc_22000', 'FSSC 22000'),
]

AUDIT_TYPES = [
    ('initial', 'Initial certification'),
    ('surveillance_1', '1. Surveillance'),
    ('surveillance_2', '2. Surveillance'),
    ('recertification', 'Re-certification'),
    ('pre_audit', 'Pre-audit'),
    ('enhancement', 'Enhancement'),
    ('others', 'Others'),
    ('self_definition', 'Self definition'),
]

EAC_SCOPES = [(code, code) for code in (
    '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16',
    '17.1', '17.2', '18', '19.1', '19.2', '20', '21', '22', '23', '24', '25', '26', '27',
    '28', '29.1', '30', '31', '32', '33', '34', '35', '36', '37', '38.1', '38.2', '39')]

TEAM_ROLES = [
    ('auditor', 'Auditor'),
    ('expert', 'Expert'),
    ('trainee', 'Trainee'),
    ('witness', 'Witness-Auditor'),
]

MAX_STANDARDS = 5

# The fixed rows of the audit schedule in the Word form.
DEFAULT_SCHEDULE = [
    {'is_section': True,
     'content': 'Location address (Remote incl. method to be specified per audit unit)'},
    {'content': 'Opening meeting\nIntroduction of all participants, Confirmation of the audit plan'},
    {'content': 'For shift work: Auditing of Shift 1 (if necessary acc. IAF MD 5)'},
    {'content': 'Break'},
    {'content': 'For shift work: Auditing of Shift 2 (if necessary acc. IAF MD 5)'},
    {'is_section': True, 'content': 'General'},
    {'content': 'Preparation of audit conclusions\nDiscussion of open questions\n'
                'Review and adjustment of findings\nCoordination of the auditors'},
    {'content': 'Closing meeting, Presentation of audit findings, Discussion'},
    {'content': 'End of audit'},
]


def default_schedule_commands():
    return [Command.create(dict(vals, sequence=10 * (i + 1)))
            for i, vals in enumerate(DEFAULT_SCHEDULE)]


class AuditInfoMixin(models.AbstractModel):
    """Sections "1. Company information" and "2. Audit information", which open almost every
    TUV Austria audit form (audit plans, audit report, checklists, participation list...).

    Shared by the standalone forms (Reports cards) and the project (Audit Plan tab), hence the
    ap_ prefix: project.project already has a partner_id, company_id, name... On a project the
    fields exist once, so every form of that audit shows the same company and audit data.
    The standards and team tables are One2many fields, which need their own inverse field, so
    each model using the mixin declares ap_standard_line_ids and ap_team_line_ids itself.
    """

    _name = 'tuv.audit.info.mixin'
    _description = 'Audit Form: Company and Audit Information'

    # 1. Company information
    ap_partner_id = fields.Many2one('res.partner', string='Company Name')
    ap_company_address = fields.Text(string='Address', compute='_compute_ap_company_address',
                                     store=True, readonly=False)
    ap_other_sites = fields.Text(string='Other Audited Sites')
    ap_representative = fields.Char(string='Company Representative')
    ap_representative_email = fields.Char(string='E-mail')
    ap_certificate_scope = fields.Text(string='Scope of Application / Certificate Text')

    # 2. Audit information
    ap_audit_date_stage1 = fields.Date(string='Audit Date Stage 1')
    ap_audit_date_stage2 = fields.Date(string='Audit Date Stage 2')
    ap_audit_date_until = fields.Date(string='Until')
    ap_remote = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('partly', 'Partly')],
                                 string='Remote', default='no')
    ap_audit_method = fields.Selection(AUDIT_METHODS, string='Audit Method')
    ap_audit_method_other = fields.Char(string='Audit Method (Own Definition)')
    ap_employee_count = fields.Integer(string='No. of Employees')
    ap_employee_scope_count = fields.Integer(string='No. of Employees in Scope')
    ap_audit_duration_hours = fields.Float(string='Audit Duration in Hours')
    ap_standards_display = fields.Char(string='Standards', compute='_compute_ap_standards',
                                       store=True)
    ap_standard_count = fields.Integer(string='No. of Standards', compute='_compute_ap_standards',
                                       store=True)
    ap_scope_change = fields.Selection([
        ('no_changes', 'No changes'),
        ('adjustment', 'Adjustment required'),
    ], string='Scope', default='no_changes')
    ap_eac_scope = fields.Selection(EAC_SCOPES, string='EAC Scope')
    ap_nace_code = fields.Char(string='NACE Code (only for EMAS)')
    ap_category = fields.Char(string='Category (ISO 22003 / ISO 13485)')
    ap_lead_auditor_id = fields.Many2one('res.partner', string='Lead Auditor')
    ap_auditor_names = fields.Char(string='Auditor(s)', compute='_compute_ap_auditor_names',
                                   store=True, readonly=False)

    @api.depends('ap_partner_id')
    def _compute_ap_company_address(self):
        for rec in self:
            rec.ap_company_address = (rec.ap_partner_id._display_address(without_company=True)
                                      if rec.ap_partner_id else False)

    @api.depends('ap_standard_line_ids.standard')
    def _compute_ap_standards(self):
        labels = dict(STANDARDS)
        for rec in self:
            rec.ap_standards_display = ', '.join(
                labels[s] for s in rec.ap_standard_line_ids.mapped('standard') if s)
            rec.ap_standard_count = len(rec.ap_standard_line_ids)

    @api.depends('ap_team_line_ids.partner_id')
    def _compute_ap_auditor_names(self):
        for rec in self:
            rec.ap_auditor_names = ', '.join(rec.ap_team_line_ids.partner_id.mapped('name'))

    @api.constrains('ap_standard_line_ids')
    def _check_ap_standard_count(self):
        for rec in self:
            if len(rec.ap_standard_line_ids) > MAX_STANDARDS:
                raise ValidationError(_('An audit plan holds at most %s standards.', MAX_STANDARDS))

    @api.constrains('ap_audit_date_stage1', 'ap_audit_date_stage2', 'ap_audit_date_until')
    def _check_ap_dates(self):
        for rec in self:
            if rec.ap_audit_date_stage1 and rec.ap_audit_date_stage2 \
                    and rec.ap_audit_date_stage2 < rec.ap_audit_date_stage1:
                raise ValidationError(_('Audit plan: Stage 2 cannot be before Stage 1.'))
            start = rec.ap_audit_date_stage2 or rec.ap_audit_date_stage1
            if start and rec.ap_audit_date_until and rec.ap_audit_date_until < start:
                raise ValidationError(_('Audit plan: the "until" date cannot be before the audit date.'))

    # ------------------------------------------------------------------
    # PDF helpers (report/common_templates.xml and the form reports)
    # ------------------------------------------------------------------
    def _ap_logo_data_uri(self):
        """The TUV Austria logo of the Word form, inlined so the PDF never fetches it over HTTP."""
        with file_open('tuv_audit_reports/static/src/img/tuv_logo.jpeg', 'rb') as logo:
            return 'data:image/jpeg;base64,' + base64.b64encode(logo.read()).decode()

    @api.model
    def _ap_time_range(self, line):
        """'09:00 - 10:30' from the schedule line's float hours, '' when none is set."""
        def fmt(value):
            hours, minutes = divmod(round(value * 60), 60)
            return '%02d:%02d' % (hours, minutes)
        if not (line.time_from or line.time_to):
            return ''
        if line.time_from and line.time_to:
            return '%s - %s' % (fmt(line.time_from), fmt(line.time_to))
        return fmt(line.time_from or line.time_to)

    @api.model
    def _ap_schedule_blocks(self, line):
        """The content of a schedule row as blocks to print: ('h', text, colour) for a bold
        line, ('ul', [texts]) for a run of bullets. Notation: "- " starts a bullet,
        "[blue]" / "[red]" a coloured heading. Rows written without any "- " (the audit plan's
        own rows) keep their old reading: first line bold, the next lines bullets."""
        texts = [t.strip() for t in (line.content or '').split('\n') if t.strip()]
        explicit = any(t.startswith('- ') for t in texts)
        colours = (('[blue]', '#0000FF'), ('[red]', '#C00000'), ('[green]', '#00B050'))
        blocks = []
        for i, text in enumerate(texts):
            if text.startswith('- ') if explicit else i > 0:
                item = text[2:] if text.startswith('- ') else text
                if blocks and blocks[-1][0] == 'ul':
                    blocks[-1][1].append(item)
                else:
                    blocks.append(('ul', [item]))
                continue
            colour = False
            for tag, value in colours:
                if text.startswith(tag):
                    text, colour = text[len(tag):].strip(), value
            blocks.append(('h', text, colour))
        return blocks

    @api.model
    def _ap_schedule_title(self, line):
        """The first line of a schedule row without its colour tag."""
        first = next((t.strip() for t in (line.content or '').split('\n') if t.strip()), '')
        for tag in ('[blue]', '[red]', '[green]'):
            first = first.replace(tag, '', 1)
        return first.strip()

    @api.model
    def _ap_split_at_general(self, lines):
        """Schedule rows split the way the Word form is: up to and including the "General"
        bar on one page, the rest on the next. No such bar: everything in the first part."""
        for i, line in enumerate(lines):
            if line.is_section and (line.content or '').strip() == 'General':
                return lines[:i + 1], lines[i + 1:]
        return lines, lines.browse()


class AuditPlanMixin(models.AbstractModel):
    """The audit plan form FM-TAGMBH-MSZ-001 past its sections 1 and 2: general, the audit
    schedule (ap_schedule_line_ids, declared by each model), signatures, significant issues."""

    _name = 'tuv.audit.plan.mixin'
    _description = 'Audit Plan Fields'

    # General
    ap_audit_language = fields.Selection([('german', 'German'), ('english', 'English')],
                                         string='Audit Language', default='english')

    # Signatures
    ap_sign_place = fields.Char(string='Place')
    ap_sign_date = fields.Date(string='Date')
    ap_lead_auditor_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    ap_auditor_signature = fields.Binary(string='Auditor(s) Signature', copy=False)

    # Significant issues impacting on the audit plan
    ap_significant_issues = fields.Text(string='Significant Issues Impacting on the Audit Plan')
    ap_customer_confirmed = fields.Boolean(
        string='The audit plan has been confirmed by the customer', copy=False)

    def _ap_schedule_pages(self):
        self.ensure_one()
        return self._ap_split_at_general(self.ap_schedule_line_ids)


class AuditPlan(models.Model):
    """Holder of the standalone forms: one predefined record per Reports card, each opened
    with its own form view. It carries every form's fields, as the project does."""

    _name = 'tuv.audit.plan'
    _description = 'Audit Form'
    _inherit = ['tuv.audit.info.mixin', 'tuv.audit.plan.mixin']
    _order = 'id desc'

    name = fields.Char(string='Form', required=True, readonly=True, default='Audit Plan')
    form_subtitle = fields.Char(string='Subtitle', readonly=True)
    form_reference = fields.Char(string='Form Number / Revision', readonly=True)
    # same names as on the project, so the form blocks work on both models
    audit_report_key = fields.Char(string='Form Key', readonly=True)
    audit_report_uses_info = fields.Boolean(string='Company and Audit Information', default=True)
    company_id = fields.Many2one('res.company', string='TUV Company', required=True,
                                 default=lambda self: self.env.company)
    ap_standard_line_ids = fields.One2many('tuv.audit.plan.standard', 'plan_id',
                                           string='Audit Standard(s)', copy=True)
    ap_team_line_ids = fields.One2many('tuv.audit.plan.team', 'plan_id', string='Audit Team',
                                       copy=True)
    ap_schedule_line_ids = fields.One2many('tuv.audit.plan.schedule', 'plan_id',
                                           string='Audit Schedule', copy=True,
                                           domain=[('schedule_kind', '=', 'plan')],
                                           default=lambda self: default_schedule_commands())


class AuditPlanStandard(models.Model):
    """One standard column of the audit plan: standard, audit type, registration no."""

    _name = 'tuv.audit.plan.standard'
    _description = 'Audit Plan Standard'
    _order = 'sequence, id'

    # a line belongs either to the standalone plan or to a project's Audit Plan tab
    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    standard = fields.Selection(STANDARDS, string='Standard', required=True)
    audit_type = fields.Selection(AUDIT_TYPES, string='Audit Type')
    audit_type_other = fields.Char(string='Audit Type (Own Definition)')
    registration_no = fields.Char(string='Registration No.')


class AuditPlanTeam(models.Model):
    """A member of the audit team besides the lead auditor."""

    _name = 'tuv.audit.plan.team'
    _description = 'Audit Plan Team Member'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    partner_id = fields.Many2one('res.partner', string='Name', required=True)
    role = fields.Selection(TEAM_ROLES, string='Role', required=True, default='auditor')


class AuditPlanSchedule(models.Model):
    """A row of the audit schedule (date / time, content, participants, auditors)."""

    _name = 'tuv.audit.plan.schedule'
    _description = 'Audit Plan Schedule Line'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    schedule_kind = fields.Selection([
        ('plan', 'Audit Plan'),
        ('isms', 'Audit Plan ISMS'),
    ], string='Form', required=True, default='plan', index=True)
    sequence = fields.Integer(default=10)
    is_section = fields.Boolean(string='Heading',
                                help='A heading row, e.g. the audit day with its location.')
    date = fields.Date(string='Date')
    time_from = fields.Float(string='From')
    time_to = fields.Float(string='To')
    content = fields.Text(string='Audit Content / Processes')
    participants = fields.Text(string='Department / Organizational Unit / Participants')
    auditors = fields.Char(string='Auditor(s)')
