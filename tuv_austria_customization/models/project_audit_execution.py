from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .project_task_mandays import MD_STANDARD

AUDIT_RESULT = [
    ('pending', 'Not Audited Yet'),
    ('conform', 'Conforming'),
    ('ofi', 'Opportunity for Improvement'),
    ('minor_nc', 'Minor Nonconformity'),
    ('major_nc', 'Major Nonconformity'),
    ('not_applicable', 'Not Applicable'),
]


class AuditClause(models.Model):
    """A clause of a standard the auditor has to cover on site.

    Keyed on the same standard codes as the Mandays / ATJF tab (md_standard_1..3),
    so the clauses of an audit follow straight from the standards picked there.
    """

    _name = 'tuv.audit.clause'
    _description = 'Standard Clause'
    _order = 'standard, sequence, id'
    _rec_name = 'display_code'

    standard = fields.Selection(MD_STANDARD, string='Standard', required=True, index=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(string='Clause', required=True)
    name = fields.Char(string='Title', required=True)
    active = fields.Boolean(default=True)
    display_code = fields.Char(compute='_compute_display_code')

    @api.depends('code', 'name')
    def _compute_display_code(self):
        for clause in self:
            clause.display_code = '%s %s' % (clause.code or '', clause.name or '')


class AuditChecklistLine(models.Model):
    """One clause of one audit: what the auditor found against it."""

    _name = 'tuv.audit.checklist.line'
    _description = 'Audit Checklist Line'
    _order = 'project_id, standard, sequence, id'

    project_id = fields.Many2one('project.project', required=True, ondelete='cascade', index=True)
    clause_id = fields.Many2one('tuv.audit.clause', string='Clause Ref', ondelete='restrict')
    standard = fields.Selection(MD_STANDARD, string='Standard', required=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(string='Clause', required=True)
    name = fields.Char(string='Requirement', required=True)
    result = fields.Selection(AUDIT_RESULT, string='Result', default='pending', required=True)
    evidence = fields.Text(string='Objective Evidence / Remarks')
    auditor_id = fields.Many2one(
        'res.partner', string='Audited By',
        domain="[('id', 'in', audit_team_ids)]")
    audited_on = fields.Date(string='Audited On')
    audit_team_ids = fields.Many2many(related='project_id.audit_team_ids')

    @api.onchange('result')
    def _onchange_result(self):
        for line in self:
            if line.result != 'pending' and not line.audited_on:
                line.audited_on = fields.Date.context_today(line)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    audit_state = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
    ], string='Audit Status', default='not_started', required=True, copy=False, tracking=True)
    audit_started_on = fields.Datetime(string='Audit Started On', readonly=True, copy=False)
    audit_completed_on = fields.Datetime(string='Audit Completed On', readonly=True, copy=False)
    audit_line_ids = fields.One2many(
        'tuv.audit.checklist.line', 'project_id', string='Audit Checklist', copy=False)
    # The scope the audit is run against: the client's certified scope, editable for
    # the wording the auditor confirms on site.
    audit_scope = fields.Text(
        string='Audited Scope', compute='_compute_audit_scope', store=True, readonly=False)
    audit_team_ids = fields.Many2many(
        'res.partner', compute='_compute_audit_team_ids', string='Audit Team')

    audit_pending_count = fields.Integer(compute='_compute_audit_counts', string='Not Audited')
    audit_conform_count = fields.Integer(compute='_compute_audit_counts', string='Conforming')
    audit_ofi_count = fields.Integer(compute='_compute_audit_counts', string='OFI')
    audit_minor_count = fields.Integer(compute='_compute_audit_counts', string='Minor NC')
    audit_major_count = fields.Integer(compute='_compute_audit_counts', string='Major NC')
    audit_na_count = fields.Integer(compute='_compute_audit_counts', string='Not Applicable')

    @api.depends('scope_of_certification', 'rf_scope', 'md_sale_order_id.scope_of_activity')
    def _compute_audit_scope(self):
        for project in self:
            if not project.audit_scope:
                # certified scope first, then the review form's, then the application's
                project.audit_scope = (project.scope_of_certification or project.rf_scope
                                       or project.md_sale_order_id.scope_of_activity or False)

    @api.depends('auditor_id', 'md_co_auditor_id', 'md_trainee_id')
    def _compute_audit_team_ids(self):
        for project in self:
            project.audit_team_ids = project.auditor_id | project.md_co_auditor_id | project.md_trainee_id

    @api.depends('audit_line_ids.result')
    def _compute_audit_counts(self):
        for project in self:
            results = project.audit_line_ids.mapped('result')
            project.audit_pending_count = results.count('pending')
            project.audit_conform_count = results.count('conform')
            project.audit_ofi_count = results.count('ofi')
            project.audit_minor_count = results.count('minor_nc')
            project.audit_major_count = results.count('major_nc')
            project.audit_na_count = results.count('not_applicable')

    # ------------------------------------------------------------------
    # The clauses of this audit
    # ------------------------------------------------------------------
    def _audit_standards(self):
        self.ensure_one()
        return [code for code in (self.md_standard_1, self.md_standard_2, self.md_standard_3) if code]

    def _audit_add_missing_clauses(self):
        """Put every clause of the audited standards on the checklist, once."""
        self.ensure_one()
        standards = self._audit_standards()
        clauses = self.env['tuv.audit.clause'].search([('standard', 'in', standards)])
        labels = dict(MD_STANDARD)
        without = [labels[code] for code in standards if code not in clauses.mapped('standard')]
        if without:
            raise UserError(_(
                'No clauses are set up for %s. Add them in Planning > Configuration > '
                'Audit Clauses first.', ', '.join(without)))
        present = set(self.audit_line_ids.clause_id.ids)
        self.env['tuv.audit.checklist.line'].create([{
            'project_id': self.id,
            'clause_id': clause.id,
            'standard': clause.standard,
            'sequence': clause.sequence,
            'code': clause.code,
            'name': clause.name,
            'auditor_id': self.auditor_id.id,
        } for clause in clauses if clause.id not in present])

    # ------------------------------------------------------------------
    # Start -> Complete
    # ------------------------------------------------------------------
    def action_audit_start(self):
        self.ensure_one()
        if self.atjf_state != 'reviewed':
            raise UserError(_('The audit is run as per the confirmed ATJF: approve the ATJF first.'))
        if not self._audit_standards():
            raise UserError(_('Pick the standard(s) of the audit (Standard 1-3) on the ATJF tab.'))
        if not self.ea_code_ids:
            raise UserError(_('The audit is run against the client\'s EA code scope: set the EA Code first.'))
        if not self.audit_scope:
            raise UserError(_('Write the client\'s certified scope in "Audited Scope" before starting the audit.'))
        self._audit_add_missing_clauses()
        self.write({
            'audit_state': 'in_progress',
            'audit_started_on': fields.Datetime.now(),
            'audit_completed_on': False,
        })
        self.message_post(body=_(
            'Audit started on site by %(auditor)s: %(count)s clauses of %(standards)s, '
            'EA code %(ea)s.', auditor=self.auditor_id.name, count=len(self.audit_line_ids),
            standards=self.atjf_standards, ea=', '.join(self.ea_code_ids.mapped('name'))))
        return True

    def action_audit_load_clauses(self):
        """A standard was added to the audit after it started."""
        self.ensure_one()
        self._audit_add_missing_clauses()
        return True

    def action_audit_complete(self):
        self.ensure_one()
        if self.audit_state != 'in_progress':
            raise UserError(_('Only an audit in progress can be completed.'))
        if self.atjf_state != 'reviewed':
            raise UserError(_('The ATJF was changed after the audit started and is no longer '
                              'reviewed. Have it approved again before completing the audit.'))
        pending = self.audit_line_ids.filtered(lambda l: l.result == 'pending')
        if pending:
            raise UserError(_('Every applicable clause has to be audited. Still open:\n- %s',
                              '\n- '.join('%s %s' % (l.code, l.name) for l in pending)))
        unexplained = self.audit_line_ids.filtered(
            lambda l: l.result in ('not_applicable', 'minor_nc', 'major_nc') and not l.evidence)
        if unexplained:
            raise UserError(_('Write the evidence or the reason for these clauses:\n- %s',
                              '\n- '.join('%s %s' % (l.code, l.name) for l in unexplained)))
        self.write({'audit_state': 'done', 'audit_completed_on': fields.Datetime.now()})
        self.message_post(body=_(
            'Audit completed: %(conform)s conforming, %(minor)s minor NC, %(major)s major NC, '
            '%(ofi)s OFI, %(na)s not applicable.', conform=self.audit_conform_count,
            minor=self.audit_minor_count, major=self.audit_major_count,
            ofi=self.audit_ofi_count, na=self.audit_na_count))
        return True

    def action_audit_reopen(self):
        self.ensure_one()
        self.write({'audit_state': 'in_progress', 'audit_completed_on': False})
        self.message_post(body=_('Audit reopened by %s.', self.env.user.name))
        return True
