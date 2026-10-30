from odoo import Command, api, fields, models

from .audit_checklist import checklist_data

ISMS_RATES = [
    ('FC', 'FC'),
    ('IM', 'IM'),
    ('PC', 'PC'),
    ('NC', 'NC'),
]
ISMS_KEY = 'checklist_iso27001'


def isms_line_commands():
    """One line per row of the Excel checklist FM-TAGMBH-MSZ-023 (data/checklists/iso27001.json)."""
    return [Command.create({
        'sequence': index,
        'is_chapter': row['chapter'],
        'sel': row['sel'],
        'ref': row['ref'],
        'requirement': row['requirement'],
        'rate': row['rate'] or False,
        'evidence': row['evidence'],
        'findings': row['findings'],
        'comments': row['comments'],
        'audit_notes': row['notes'],
        'capabilities': row['capabilities'],
    }) for index, row in enumerate(checklist_data('iso27001')['rows'])]


class AuditIsmsCheckLine(models.Model):
    """A row of the ISO/IEC 27001:2022 (+ 27701) audit checklist: a chapter heading or a
    requirement / control with the auditor's rate, evidence, findings and notes."""

    _name = 'tuv.form.isms.line'
    _description = 'ISMS Audit Checklist Row'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    sequence = fields.Integer(readonly=True)
    is_chapter = fields.Boolean(string='Chapter', readonly=True)
    sel = fields.Char(string='Sel.', readonly=True,
                      help='Standard the requirement comes from (27001, 27701, 27018...); '
                           '"(St.1)": to be audited in stage 1.')
    ref = fields.Char(string='Ref.', readonly=True)
    requirement = fields.Text(string='Requirement / Control', readonly=True)
    rate = fields.Selection(ISMS_RATES, string='Rate')
    evidence = fields.Text(string='Evidence')
    findings = fields.Text(string='Findings')
    comments = fields.Text(string='Comments')
    audit_notes = fields.Text(string='Audit Notes')
    capabilities = fields.Char(string='Operational Capabilities')


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = 'tuv.audit.plan'

    ic_line_ids = fields.One2many('tuv.form.isms.line', 'plan_id', string='ISMS Checklist')

    def _tuv_fill_isms_checklist(self):
        """Called from data: the rows of the Excel checklist, once."""
        for plan in self:
            if not plan.ic_line_ids:
                plan.ic_line_ids = isms_line_commands()


class ProjectProject(models.Model):
    _inherit = 'project.project'

    ic_line_ids = fields.One2many('tuv.form.isms.line', 'project_id', string='ISMS Checklist',
                                  compute='_compute_ic_line_ids', store=True, readonly=False)

    @api.depends('audit_report_id')
    def _compute_ic_line_ids(self):
        # the rows of the Excel checklist, added once that checklist is picked; entries are kept
        for project in self:
            if not project.ic_line_ids and project.audit_report_key == ISMS_KEY:
                project.ic_line_ids = isms_line_commands()
            else:
                project.ic_line_ids = project.ic_line_ids


class AuditInfoMixin(models.AbstractModel):
    _inherit = 'tuv.audit.info.mixin'

    def _ic_meta(self):
        return checklist_data('iso27001')['meta']
