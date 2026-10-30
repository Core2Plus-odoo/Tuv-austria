import functools
import json

from odoo import Command, api, fields, models
from odoo.tools import file_open

# The Word audit checklists, as converted by tools/docx_forms.py into data/checklists/<key>.json:
# the static tables of the form (texts, merged cells, grey cells) and its tick-box "elements".
CHECKLISTS = [
    ('iso9001', 'Audit Checklist ISO 9001'),
    ('iso45001', 'Audit Checklist ISO 45001'),
    ('iso14001', 'Audit Checklist ISO 14001'),
    ('iso50001', 'Audit Checklist ISO 50001'),
    ('iso13485', 'Audit Checklist ISO 13485'),
    ('iso20000', 'Audit Checklist ISO/IEC 20000-1'),
    ('iso37301', 'Audit Checklist ISO 37301'),
    ('combined', 'Audit Checklist Combined QM/EM/HSE/EN'),
    # PNAC: older revisions of the same TÜV Austria checklists
    ('pnac9001', 'PNAC Audit Checklist ISO 9001'),
    ('pnac14001', 'PNAC Audit Checklist ISO 14001'),
    ('pnac45001', 'PNAC Audit Checklist ISO 45001'),
    ('pnaccombined', 'PNAC Audit Checklist Combined QM/EM/HSE/EN'),
]
CHECKLIST_KEYS = [key for key, _name in CHECKLISTS]
REPORT_KEY_PREFIX = 'checklist_'


@functools.lru_cache(maxsize=None)
def checklist_data(key):
    with file_open('tuv_audit_reports/data/checklists/%s.json' % key) as f:
        return json.load(f)


def checklist_line_commands(key):
    """One line per tick-box element of the Word checklist, in the form's order."""
    return [Command.create({
        'checklist_key': key,
        'sequence': index,
        'group': element['group'],
        'clause': element['clause'],
        'mand_ca': element['mand'][0],
        'mand_sa1': element['mand'][1],
        'mand_sa2': element['mand'][2],
    }) for index, element in enumerate(checklist_data(key)['elements'])]


def _lines_field(inverse, key, **kwargs):
    return fields.One2many(
        'tuv.form.checklist.line', inverse, string=dict(CHECKLISTS)[key],
        domain=[('checklist_key', '=', key)], context={'default_checklist_key': key}, **kwargs)


class AuditChecklistLine(models.Model):
    """A standard element of a checklist (clause) with its three audit types: the grey ones of
    the Word form are mandatory for that audit type, the ticks are the auditor's."""

    # not tuv.audit.checklist.line: that is the 3.1 audit execution checklist of
    # tuv_austria_customization
    _name = 'tuv.form.checklist.line'
    _description = 'Audit Checklist Form Element'
    _order = 'checklist_key, sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    checklist_key = fields.Selection(CHECKLISTS, string='Checklist', required=True, index=True)
    sequence = fields.Integer(string='Element No.', readonly=True,
                              help='Position of the element in the Word form.')
    group = fields.Char(string='Standard', readonly=True)
    clause = fields.Char(string='Clause', readonly=True)
    mand_ca = fields.Boolean(string='Mandatory CA/RA', readonly=True)
    mand_sa1 = fields.Boolean(string='Mandatory 1. SA', readonly=True)
    mand_sa2 = fields.Boolean(string='Mandatory 2. SA', readonly=True)
    mandatory_for = fields.Char(string='Mandatory for', compute='_compute_mandatory_for')
    chk_ca = fields.Boolean(string='CA/RA')
    chk_sa1 = fields.Boolean(string='1. SA')
    chk_sa2 = fields.Boolean(string='2. SA')

    @api.depends('mand_ca', 'mand_sa1', 'mand_sa2')
    def _compute_mandatory_for(self):
        for line in self:
            line.mandatory_for = ', '.join(label for label, flag in (
                ('CA/RA', line.mand_ca), ('1. SA', line.mand_sa1), ('2. SA', line.mand_sa2)) if flag)


class AuditChecklistMixin(models.AbstractModel):
    """The "Notes of auditor(s)" of every checklist and the data the checklist PDF draws."""

    _name = 'tuv.audit.checklist.mixin'
    _description = 'Audit Checklist Fields'

    cl_iso9001_notes = fields.Text(string='Notes of Auditor(s) - ISO 9001')
    cl_iso45001_notes = fields.Text(string='Notes of Auditor(s) - ISO 45001')
    cl_iso14001_notes = fields.Text(string='Notes of Auditor(s) - ISO 14001')
    cl_iso50001_notes = fields.Text(string='Notes of Auditor(s) - ISO 50001')
    cl_iso13485_notes = fields.Text(string='Notes of Auditor(s) - ISO 13485')
    cl_iso20000_notes = fields.Text(string='Auditor Notice - ISO/IEC 20000-1')
    cl_iso37301_notes = fields.Text(string='Auditor Notice - ISO 37301')
    cl_combined_notes = fields.Text(string='Notes of the Auditor - Combined QM/EM/HSE/EN')
    cl_pnac9001_notes = fields.Text(string='Notes of Auditor(s) - PNAC ISO 9001')
    cl_pnac14001_notes = fields.Text(string='Notes of Auditor(s) - PNAC ISO 14001')
    cl_pnac45001_notes = fields.Text(string='Notes of Auditor(s) - PNAC ISO 45001')
    cl_pnaccombined_notes = fields.Text(string='Notes of the Auditor - PNAC Combined')

    def _cl_payload(self):
        """Everything the checklist PDF needs for the checklist selected on this record."""
        self.ensure_one()
        key = (self.audit_report_key or '').removeprefix(REPORT_KEY_PREFIX)
        data = checklist_data(key)
        lines = {line.sequence: line for line in self['cl_%s_line_ids' % key]}
        ticks, mandatory = [], []
        for index, element in enumerate(data['elements']):
            line = lines.get(index)
            ticks.append((line.chk_ca, line.chk_sa1, line.chk_sa2) if line else (False,) * 3)
            mandatory.append(element['mand'])
        return {
            'meta': data['meta'],
            'blocks': data['blocks'],
            'ticks': ticks,
            'mandatory': mandatory,
            'notes_title': data['notes_title'],
            'notes': self['cl_%s_notes' % key] or '',
        }


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = ['tuv.audit.plan', 'tuv.audit.checklist.mixin']

    cl_iso9001_line_ids = _lines_field('plan_id', 'iso9001')
    cl_iso45001_line_ids = _lines_field('plan_id', 'iso45001')
    cl_iso14001_line_ids = _lines_field('plan_id', 'iso14001')
    cl_iso50001_line_ids = _lines_field('plan_id', 'iso50001')
    cl_iso13485_line_ids = _lines_field('plan_id', 'iso13485')
    cl_iso20000_line_ids = _lines_field('plan_id', 'iso20000')
    cl_iso37301_line_ids = _lines_field('plan_id', 'iso37301')
    cl_combined_line_ids = _lines_field('plan_id', 'combined')
    cl_pnac9001_line_ids = _lines_field('plan_id', 'pnac9001')
    cl_pnac14001_line_ids = _lines_field('plan_id', 'pnac14001')
    cl_pnac45001_line_ids = _lines_field('plan_id', 'pnac45001')
    cl_pnaccombined_line_ids = _lines_field('plan_id', 'pnaccombined')

    def _tuv_fill_checklist(self):
        """Called from data: give each predefined checklist form its elements once."""
        for plan in self:
            key = (plan.audit_report_key or '').removeprefix(REPORT_KEY_PREFIX)
            if key in CHECKLIST_KEYS and not plan['cl_%s_line_ids' % key]:
                plan['cl_%s_line_ids' % key] = checklist_line_commands(key)


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'tuv.audit.checklist.mixin']

    cl_iso9001_line_ids = _lines_field('project_id', 'iso9001', compute='_compute_cl_line_ids',
                                       store=True, readonly=False)
    cl_iso45001_line_ids = _lines_field('project_id', 'iso45001', compute='_compute_cl_line_ids',
                                        store=True, readonly=False)
    cl_iso14001_line_ids = _lines_field('project_id', 'iso14001', compute='_compute_cl_line_ids',
                                        store=True, readonly=False)
    cl_iso50001_line_ids = _lines_field('project_id', 'iso50001', compute='_compute_cl_line_ids',
                                        store=True, readonly=False)
    cl_iso13485_line_ids = _lines_field('project_id', 'iso13485', compute='_compute_cl_line_ids',
                                        store=True, readonly=False)
    cl_iso20000_line_ids = _lines_field('project_id', 'iso20000', compute='_compute_cl_line_ids',
                                        store=True, readonly=False)
    cl_iso37301_line_ids = _lines_field('project_id', 'iso37301', compute='_compute_cl_line_ids',
                                        store=True, readonly=False)
    cl_combined_line_ids = _lines_field('project_id', 'combined', compute='_compute_cl_line_ids',
                                        store=True, readonly=False)
    cl_pnac9001_line_ids = _lines_field('project_id', 'pnac9001', compute='_compute_cl_line_ids',
                                        store=True, readonly=False)
    cl_pnac14001_line_ids = _lines_field('project_id', 'pnac14001', compute='_compute_cl_line_ids',
                                         store=True, readonly=False)
    cl_pnac45001_line_ids = _lines_field('project_id', 'pnac45001', compute='_compute_cl_line_ids',
                                         store=True, readonly=False)
    cl_pnaccombined_line_ids = _lines_field('project_id', 'pnaccombined', compute='_compute_cl_line_ids',
                                            store=True, readonly=False)

    @api.depends('audit_report_id')
    def _compute_cl_line_ids(self):
        # the elements of the Word checklist, added once that checklist is picked; ticks are kept
        for project in self:
            selected = (project.audit_report_key or '').removeprefix(REPORT_KEY_PREFIX)
            for key in CHECKLIST_KEYS:
                fname = 'cl_%s_line_ids' % key
                if key == selected and not project[fname]:
                    project[fname] = checklist_line_commands(key)
                else:
                    project[fname] = project[fname]
