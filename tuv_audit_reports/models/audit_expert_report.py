from odoo import Command, api, fields, models

# The requirements of the "technical assessment" table of form FM-TAGMBH-MSZ-004, then the two
# free rows the form leaves for further requirements.
EXPERT_REQUIREMENTS = [
    'Legal requirements',
    'Customary regulations',
    'Personnel qualification',
    'Equipment and facilities',
    'Information/Documentation',
    'Records',
    'Hygiene',
    '',
    '',
]


def expert_requirement_commands():
    return [Command.create({'sequence': 10 * (i + 1), 'name': name})
            for i, name in enumerate(EXPERT_REQUIREMENTS)]


class AuditExpertRequirement(models.Model):
    """A row of the expert's technical assessment: requirement, result, comments."""

    _name = 'tuv.audit.expert.requirement'
    _description = 'Expert Report Requirement'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Requirement')
    result = fields.Selection([
        ('fulfilled', 'fulfilled'),
        ('not_fulfilled', 'not fulfilled'),
        ('not_applicable', 'not applicable'),
    ], string='Result')
    comments = fields.Char(string='Comments')


class AuditExpertReportMixin(models.AbstractModel):
    """Expert report, form FM-TAGMBH-MSZ-004, past its sections 1 and 2."""

    _name = 'tuv.audit.expert.report.mixin'
    _description = 'Expert Report Fields'

    er_supplementary = fields.Text(string='Supplementary Statement (comments/findings), if any')
    er_place = fields.Char(string='Place')
    er_date = fields.Date(string='Date')
    er_expert_id = fields.Many2one('res.partner', string='Expert')
    er_expert_signature = fields.Binary(string='Signature of Expert', copy=False)


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = ['tuv.audit.plan', 'tuv.audit.expert.report.mixin']

    er_requirement_ids = fields.One2many('tuv.audit.expert.requirement', 'plan_id',
                                         string='Technical Assessment', copy=True)

    def _tuv_fill_expert_requirements(self):
        """Called from data: the requirement rows of the Word form, once."""
        for plan in self:
            if not plan.er_requirement_ids:
                plan.er_requirement_ids = expert_requirement_commands()


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'tuv.audit.expert.report.mixin']

    er_requirement_ids = fields.One2many(
        'tuv.audit.expert.requirement', 'project_id', string='Technical Assessment',
        compute='_compute_er_requirement_ids', store=True, readonly=False)
    er_expert_id = fields.Many2one(compute='_compute_er_expert_id', store=True, readonly=False)

    @api.depends('audit_report_id')
    def _compute_er_requirement_ids(self):
        # the requirement rows of the Word form, added once the expert report is picked
        for project in self:
            if not project.er_requirement_ids and project.audit_report_key == 'expert_report':
                project.er_requirement_ids = expert_requirement_commands()
            else:
                project.er_requirement_ids = project.er_requirement_ids

    @api.depends('ap_team_line_ids.partner_id', 'ap_team_line_ids.role')
    def _compute_er_expert_id(self):
        # the expert of the audit team (section 2)
        for project in self:
            experts = project.ap_team_line_ids.filtered(lambda l: l.role == 'expert')
            project.er_expert_id = experts[:1].partner_id or project.er_expert_id
