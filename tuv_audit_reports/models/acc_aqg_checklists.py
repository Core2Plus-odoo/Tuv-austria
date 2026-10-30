import functools
import json

from odoo import Command, api, fields, models
from odoo.tools import file_open

# The AQG audit questionnaires / checklists of ESYD, PNAC and SAAC, converted by
# tools/aqg_forms.py into data/checklists/<key>.json: the Word body (tables cell by cell, with
# the paragraphs of a cell and the tables nested in it) and the "lines" the auditor fills in.
# key: (field part, lists of lines the form has)
AQG_FORMS = {
    'aqg_esyd_27001': ('esyd_27001', ('objective', 'clause', 'legal', 'evidence')),
    'aqg_esyd_9001_14001_45001': ('esyd_9001_14001_45001', ('objective', 'clause', 'legal', 'evidence')),
    'aqg_esyd_9001_14001': ('esyd_9001_14001', ('objective', 'clause', 'legal', 'evidence')),
    'aqg_9001_22000': ('9001_22000', ('objective', 'clause', 'legal', 'evidence')),
    'aqg_pnac_22000': ('pnac_22000', ('clause', 'legal')),
    'aqg_saac_9001': ('saac_9001', ('element',)),
}
AQG_KEYS = [
    ('aqg_esyd_27001', 'ESYD Audit Questionnaire ISO 27001'),
    ('aqg_esyd_9001_14001_45001', 'ESYD Audit Questionnaire ISO 9001/14001/45001'),
    ('aqg_esyd_9001_14001', 'ESYD Audit Questionnaire ISO 9001/14001'),
    ('aqg_9001_22000', 'Audit Questionnaire ISO 9001/22000'),
    ('aqg_pnac_22000', 'PNAC Audit Questionnaire ISO 22000'),
    ('aqg_saac_9001', 'SAAC Audit Checklist ISO 9001'),
]
AQG_LISTS = [
    ('objective', 'Audit Objective'),
    ('clause', 'Standard Requirements'),
    ('legal', 'Legislative Requirements'),
    ('evidence', 'Evidence'),
    ('element', 'Standard Elements per Audit Type'),
]


@functools.lru_cache(maxsize=None)
def aqg_data(key):
    with file_open('tuv_audit_reports/data/checklists/%s.json' % key) as f:
        return json.load(f)


def aqg_field(key, list_key):
    return 'aqg_%s_%s_ids' % (AQG_FORMS[key][0], list_key)


def aqg_line_commands(key, list_key):
    """The lines of one list of the Word form, with the form's own ticks / texts as defaults."""
    commands = []
    for index, line in enumerate(aqg_data(key)['lines']):
        if line['list'] != list_key:
            continue
        vals = {
            'checklist_key': key, 'list_key': list_key, 'sequence': index,
            'section': line['section'], 'label': line['label'], 'ref': line['ref'],
        }
        for i in range(3):
            vals['box_%d' % (i + 1)] = line['box'][i]
            vals['mand_%d' % (i + 1)] = line['mand'][i]
            vals['text_%d' % (i + 1)] = line['text'][i]
        commands.append(Command.create(vals))
    return commands


def _lines_field(inverse, key, list_key, **kwargs):
    return fields.One2many(
        'tuv.form.aqg.line', inverse, string=dict(AQG_LISTS)[list_key],
        domain=[('checklist_key', '=', key), ('list_key', '=', list_key)],
        context={'default_checklist_key': key, 'default_list_key': list_key}, **kwargs)


def _project_lines_field(key, list_key):
    return _lines_field('project_id', key, list_key, compute='_compute_aqg_line_ids',
                        store=True, readonly=False)


# ------------------------------------------------------------------------------------------
# PDF: the JSON blocks with the inputs replaced by what was filled in
# ------------------------------------------------------------------------------------------
def _value_paras(text, like=None):
    """What was typed in, one paragraph per line, in the size and alignment of the Word field
    (not its colour or weight: Word's prompts are grey, labels bold)."""
    style = ' '.join(s.strip() + ';' for s in ((like or {}).get('st') or '').split(';')
                     if s.strip().startswith(('font-size', 'text-align'))) or None
    return [{'parts': [[None, t]], 'st': style} for t in (text or '').split('\n')] if text else []


class _Resolver:
    def __init__(self, record, key):
        part, lists = AQG_FORMS[key]
        self.defaults = aqg_data(key)['lines']
        self.lines = {}
        for list_key in lists:
            for line in record[aqg_field(key, list_key)]:
                self.lines[line.sequence] = line
        self.ap = record._aqg_ap_values()
        self.record, self.part = record, part

    def value(self, ref):
        seq, attr = ref
        line = self.lines.get(seq)
        if line:
            return line[attr]
        default = self.defaults[seq]
        return default['box' if attr.startswith('box') else 'text'][int(attr[-1]) - 1]

    def field(self, name):
        fname = 'aqg_%s_%s' % (self.part, name)
        return (self.record[fname] or '') if fname in self.record._fields else ''

    def box(self, box):
        if isinstance(box, dict):
            return bool(self.value(box['in'])) if 'in' in box else bool(self.ap.get(box['ap']))
        return box

    def paragraph(self, p):
        if 'tbl' in p:
            return [{'tbl': self.table(p['tbl'])}]
        out = dict(p, parts=[[self.box(b), t] for b, t in p['parts']])
        if p.get('ap'):
            value = self.ap.get(p['ap']) or ''
            if value:
                out['parts'][-1] = [out['parts'][-1][0], out['parts'][-1][1] + ' ' + value]
        if p.get('in'):
            return [out] + _value_paras(self.value(p['in']), p)
        return [out]

    def paragraphs(self, ps):
        return [q for p in ps for q in self.paragraph(p)]

    def cell(self, c):
        out = dict(c)
        like = next((p for p in c['ps'] if 'parts' in p), None)
        if c.get('f'):
            out['ps'] = _value_paras(self.field(c['f']), like)
        elif c.get('in') and c['in'][1].startswith('box'):
            out['ps'] = [{'parts': [[bool(self.value(c['in'])), '']], 'st': 'text-align: center;'}]
        elif c.get('in'):
            out['ps'] = _value_paras(self.value(c['in']), like)
        else:
            out['ps'] = self.paragraphs(c['ps'])
            if c.get('ap'):
                out['ps'] += _value_paras(self.ap.get(c['ap']) or '', like)
        return out

    def table(self, t):
        return dict(t, rows=[dict(r, cells=[self.cell(c) for c in r['cells']]) for r in t['rows']])

    def blocks(self, b):
        if b['type'] == 'table':
            return self.split(self.table(b))
        if b['type'] == 'p':
            return [{'type': 'ps', 'ps': self.paragraph(b['p'])}]
        if b['type'] == 'checks':
            lines = [t.strip() for t in self.field(b['f']).split('\n') if t.strip()]
            return [{'type': 'checks', 'items': lines}]
        return [b]

    @staticmethod
    def split(table):
        """A row starting a new page in Word ("ANNEX A"): the table goes on in a new table
        after a page break, with the header rows again (a <tr> does not break reliably)."""
        head = table['rows'][:table['head']]
        out, rows = [], []
        for row in table['rows'][table['head']:]:
            if row.get('pb') and rows:
                out += [dict(table, rows=head + rows), {'type': 'pagebreak'}]
                rows = []
            rows.append(row)
        return out + [dict(table, rows=head + rows)]


class AqgLine(models.Model):
    """A line of an AQG questionnaire: a tick box (audit objective, standard requirement), a
    legislative requirement, the evidence of a requirement per standard or (SAAC) an element
    ticked per audit type. Where the Word form holds example evidence, that is the default."""

    _name = 'tuv.form.aqg.line'
    _description = 'Audit Questionnaire Line'
    _order = 'checklist_key, list_key, sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    checklist_key = fields.Selection(AQG_KEYS, string='Form', required=True, index=True)
    list_key = fields.Selection(AQG_LISTS, string='Part', required=True, index=True)
    sequence = fields.Integer(readonly=True, help='Position of the input in the Word form.')
    section = fields.Char(string='Section', readonly=True)
    label = fields.Text(string='Requirement', readonly=True)
    ref = fields.Char(string='Reference', readonly=True,
                      help='Mandatory documents / clauses (MDE, MDI, RDI) of the row.')
    box_1 = fields.Boolean(string='Checked')
    box_2 = fields.Boolean(string='1. SA')
    box_3 = fields.Boolean(string='2. SA')
    mand_1 = fields.Boolean(string='Mandatory CA/RA', readonly=True)
    mand_2 = fields.Boolean(string='Mandatory 1. SA', readonly=True)
    mand_3 = fields.Boolean(string='Mandatory 2. SA', readonly=True)
    mandatory_for = fields.Char(string='Mandatory for', compute='_compute_mandatory_for')
    text_1 = fields.Text(string='Text 1')
    text_2 = fields.Text(string='Text 2')
    text_3 = fields.Text(string='Text 3')

    @api.depends('mand_1', 'mand_2', 'mand_3')
    def _compute_mandatory_for(self):
        for line in self:
            line.mandatory_for = ', '.join(label for label, flag in (
                ('CA/RA', line.mand_1), ('1. SA', line.mand_2), ('2. SA', line.mand_3)) if flag)


class AqgMixin(models.AbstractModel):
    """Free texts of the AQG forms (auditor notes, improvement hints, positive findings) and
    the data their PDF draws."""

    _name = 'tuv.form.aqg.mixin'
    _description = 'Audit Questionnaire Fields'

    aqg_esyd_27001_notes = fields.Text(string='Auditor Notes - ESYD ISO 27001')
    aqg_esyd_27001_hints = fields.Text(string='List of Improvement Hints - ESYD ISO 27001')
    aqg_esyd_27001_findings = fields.Text(string='List of Positive Findings - ESYD ISO 27001')
    aqg_esyd_9001_14001_45001_notes = fields.Text(string='Auditor Notes - ESYD ISO 9001/14001/45001')
    aqg_esyd_9001_14001_45001_hints = fields.Text(string='List of Improvement Hints - ESYD ISO 9001/14001/45001')
    aqg_esyd_9001_14001_45001_findings = fields.Text(string='List of Positive Findings - ESYD ISO 9001/14001/45001')
    aqg_esyd_9001_14001_notes = fields.Text(string='Auditor Notes - ESYD ISO 9001/14001')
    aqg_esyd_9001_14001_hints = fields.Text(string='List of Improvement Hints - ESYD ISO 9001/14001')
    aqg_esyd_9001_14001_findings = fields.Text(string='List of Positive Findings - ESYD ISO 9001/14001')
    aqg_9001_22000_notes = fields.Text(string='Auditor Notes - ISO 9001/22000')
    aqg_9001_22000_hints = fields.Text(string='List of Improvement Hints - ISO 9001/22000')
    aqg_9001_22000_findings = fields.Text(string='List of Positive Findings - ISO 9001/22000')
    aqg_pnac_22000_notes = fields.Text(string='Auditor Notes - PNAC ISO 22000')
    aqg_pnac_22000_hints = fields.Text(string='List of Improvement Hints - PNAC ISO 22000')
    aqg_pnac_22000_findings = fields.Text(string='List of Positive Findings - PNAC ISO 22000')
    aqg_saac_9001_notes = fields.Text(string='Notes of Auditor(s) - SAAC ISO 9001')

    def _aqg_payload(self):
        """Everything the PDF needs for the AQG form selected on this record."""
        self.ensure_one()
        key = self.audit_report_key
        data = aqg_data(key)
        resolver = _Resolver(self, key)
        return {'meta': data['meta'], 'blocks': [out for b in data['blocks'] for out in resolver.blocks(b)]}

    def _aqg_ap_values(self):
        """Sections 1 and 2 of the Word forms, by the keys tools/aqg_forms.py bound their
        cells to: the ap_* fields as printed text."""
        self.ensure_one()

        def label(record, fname):
            if not record or not record[fname]:
                return ''
            return dict(record._fields[fname]._description_selection(self.env)).get(record[fname], '')

        def date(value):
            return value.strftime('%d.%m.%Y') if value else ''

        def own(record, fname):
            # "Others" / "Self definition" print the user's own wording
            if record and record[fname] in ('others', 'self_definition') and record[fname + '_other']:
                return record[fname + '_other']
            return label(record, fname)

        stds = self.ap_standard_line_ids.sorted(lambda s: (s.sequence, s.id))
        first = stds[:1]
        audit_type = first.audit_type or ''
        start = self.ap_audit_date_stage2 or self.ap_audit_date_stage1
        period = ' until '.join(filter(None, [date(start), date(self.ap_audit_date_until)]))
        initial = not audit_type or audit_type in ('initial', 'pre_audit', 'enhancement')
        team = self.ap_team_line_ids.sorted(lambda t: (t.sequence, t.id))
        auditors = team.filtered(lambda t: t.role == 'auditor').partner_id.mapped('name')
        values = {
            'partner': self.ap_partner_id.name or '',
            'address': ', '.join(p.strip(' ,') for p in (self.ap_company_address or '').split('\n') if p.strip(' ,')),
            'sites': self.ap_other_sites or '',
            'representative': self.ap_representative or '',
            'scope': self.ap_certificate_scope or '',
            'stage1': date(self.ap_audit_date_stage1) if initial else '',
            'stage2': date(self.ap_audit_date_stage2) if initial else '',
            'until': date(self.ap_audit_date_until),
            'surveillance': period if audit_type.startswith('surveillance') else '',
            'recertification': period if audit_type == 'recertification' else '',
            'remote': label(self, 'ap_remote'),
            'audit_type': own(first, 'audit_type'),
            'method': own(self, 'ap_audit_method'),
            'employees': str(self.ap_employee_count or ''),
            'employees_scope': str(self.ap_employee_scope_count or self.ap_employee_count or ''),
            'duration': ('%g h' % self.ap_audit_duration_hours) if self.ap_audit_duration_hours else '',
            'language': label(self, 'ap_audit_language') if 'ap_audit_language' in self._fields else '',
            'scope_nochange': self.ap_scope_change == 'no_changes',
            'scope_adjust': self.ap_scope_change == 'adjustment',
            'eac': self.ap_eac_scope or '',
            'nace': self.ap_nace_code or '',
            'category': self.ap_category or '',
            'lead': self.ap_lead_auditor_id.name or '',
            'expert': ', '.join(team.filtered(lambda t: t.role == 'expert').partner_id.mapped('name')),
            'other': ', '.join('%s (%s)' % (t.partner_id.name, label(t, 'role'))
                               for t in team.filtered(lambda t: t.role in ('trainee', 'witness'))),
        }
        # standards: "std:2" one column, "std:4+" the 4th and the further ones
        for n in range(1, 7):
            line = stds[n - 1:n]
            values['std:%d' % n] = label(line, 'standard')
            values['stdtype:%d' % n] = own(line, 'audit_type')
            values['stdreg:%d' % n] = line.registration_no or ''
            values['std:%d+' % n] = ', '.join(label(s, 'standard') for s in stds[n - 1:])
        # team columns "team:i:n": the i-th auditor, the last column takes the rest
        for n in range(1, 5):
            for i in range(n):
                names = auditors[i:] if i == n - 1 else auditors[i:i + 1]
                values['team:%d:%d' % (i, n)] = ', '.join(names)
        # PNAC "Audit date(s)": date and stage, three times
        if initial:
            dates = [(self.ap_audit_date_stage1, 'Stage 1'), (self.ap_audit_date_stage2, 'Stage 2'),
                     (self.ap_audit_date_until, 'until')]
        else:
            dates = [(start, label(first, 'audit_type')), (self.ap_audit_date_until, 'until'), (False, '')]
        for k, (day, stage) in enumerate(dates, start=1):
            values['pdate:%d' % k] = date(day)
            values['pstage:%d' % k] = stage if day else ''
        return values


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = ['tuv.audit.plan', 'tuv.form.aqg.mixin']

    aqg_esyd_27001_objective_ids = _lines_field('plan_id', 'aqg_esyd_27001', 'objective')
    aqg_esyd_27001_clause_ids = _lines_field('plan_id', 'aqg_esyd_27001', 'clause')
    aqg_esyd_27001_legal_ids = _lines_field('plan_id', 'aqg_esyd_27001', 'legal')
    aqg_esyd_27001_evidence_ids = _lines_field('plan_id', 'aqg_esyd_27001', 'evidence')
    aqg_esyd_9001_14001_45001_objective_ids = _lines_field('plan_id', 'aqg_esyd_9001_14001_45001', 'objective')
    aqg_esyd_9001_14001_45001_clause_ids = _lines_field('plan_id', 'aqg_esyd_9001_14001_45001', 'clause')
    aqg_esyd_9001_14001_45001_legal_ids = _lines_field('plan_id', 'aqg_esyd_9001_14001_45001', 'legal')
    aqg_esyd_9001_14001_45001_evidence_ids = _lines_field('plan_id', 'aqg_esyd_9001_14001_45001', 'evidence')
    aqg_esyd_9001_14001_objective_ids = _lines_field('plan_id', 'aqg_esyd_9001_14001', 'objective')
    aqg_esyd_9001_14001_clause_ids = _lines_field('plan_id', 'aqg_esyd_9001_14001', 'clause')
    aqg_esyd_9001_14001_legal_ids = _lines_field('plan_id', 'aqg_esyd_9001_14001', 'legal')
    aqg_esyd_9001_14001_evidence_ids = _lines_field('plan_id', 'aqg_esyd_9001_14001', 'evidence')
    aqg_9001_22000_objective_ids = _lines_field('plan_id', 'aqg_9001_22000', 'objective')
    aqg_9001_22000_clause_ids = _lines_field('plan_id', 'aqg_9001_22000', 'clause')
    aqg_9001_22000_legal_ids = _lines_field('plan_id', 'aqg_9001_22000', 'legal')
    aqg_9001_22000_evidence_ids = _lines_field('plan_id', 'aqg_9001_22000', 'evidence')
    aqg_pnac_22000_clause_ids = _lines_field('plan_id', 'aqg_pnac_22000', 'clause')
    aqg_pnac_22000_legal_ids = _lines_field('plan_id', 'aqg_pnac_22000', 'legal')
    aqg_saac_9001_element_ids = _lines_field('plan_id', 'aqg_saac_9001', 'element')

    def _tuv_fill_aqg(self):
        """Called from data: give each predefined AQG form its lines once."""
        for plan in self:
            key = plan.audit_report_key
            for list_key in AQG_FORMS.get(key, ('', ()))[1]:
                fname = aqg_field(key, list_key)
                if not plan[fname]:
                    plan[fname] = aqg_line_commands(key, list_key)


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'tuv.form.aqg.mixin']

    aqg_esyd_27001_objective_ids = _project_lines_field('aqg_esyd_27001', 'objective')
    aqg_esyd_27001_clause_ids = _project_lines_field('aqg_esyd_27001', 'clause')
    aqg_esyd_27001_legal_ids = _project_lines_field('aqg_esyd_27001', 'legal')
    aqg_esyd_27001_evidence_ids = _project_lines_field('aqg_esyd_27001', 'evidence')
    aqg_esyd_9001_14001_45001_objective_ids = _project_lines_field('aqg_esyd_9001_14001_45001', 'objective')
    aqg_esyd_9001_14001_45001_clause_ids = _project_lines_field('aqg_esyd_9001_14001_45001', 'clause')
    aqg_esyd_9001_14001_45001_legal_ids = _project_lines_field('aqg_esyd_9001_14001_45001', 'legal')
    aqg_esyd_9001_14001_45001_evidence_ids = _project_lines_field('aqg_esyd_9001_14001_45001', 'evidence')
    aqg_esyd_9001_14001_objective_ids = _project_lines_field('aqg_esyd_9001_14001', 'objective')
    aqg_esyd_9001_14001_clause_ids = _project_lines_field('aqg_esyd_9001_14001', 'clause')
    aqg_esyd_9001_14001_legal_ids = _project_lines_field('aqg_esyd_9001_14001', 'legal')
    aqg_esyd_9001_14001_evidence_ids = _project_lines_field('aqg_esyd_9001_14001', 'evidence')
    aqg_9001_22000_objective_ids = _project_lines_field('aqg_9001_22000', 'objective')
    aqg_9001_22000_clause_ids = _project_lines_field('aqg_9001_22000', 'clause')
    aqg_9001_22000_legal_ids = _project_lines_field('aqg_9001_22000', 'legal')
    aqg_9001_22000_evidence_ids = _project_lines_field('aqg_9001_22000', 'evidence')
    aqg_pnac_22000_clause_ids = _project_lines_field('aqg_pnac_22000', 'clause')
    aqg_pnac_22000_legal_ids = _project_lines_field('aqg_pnac_22000', 'legal')
    aqg_saac_9001_element_ids = _project_lines_field('aqg_saac_9001', 'element')

    @api.depends('audit_report_id')
    def _compute_aqg_line_ids(self):
        # the lines of the Word form, added once that form is picked; entries are kept
        for project in self:
            selected = project.audit_report_key
            for key, (_part, lists) in AQG_FORMS.items():
                for list_key in lists:
                    fname = aqg_field(key, list_key)
                    if key == selected and not project[fname]:
                        project[fname] = aqg_line_commands(key, list_key)
                    else:
                        project[fname] = project[fname]
