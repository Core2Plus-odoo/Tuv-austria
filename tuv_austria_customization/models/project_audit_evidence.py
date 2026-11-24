import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError

EVIDENCE_CATEGORY = [
    ('attendance_sheet', 'Attendance Sheet'),
    ('audit_checklist', 'Audit Checklist'),
    ('client_documents', 'Client Documents Reviewed'),
    ('other', 'Other Supporting Evidence'),
]
# What every audit file must hold before its report can be submitted.
REQUIRED_CATEGORIES = ('attendance_sheet', 'audit_checklist', 'client_documents')


class AuditEvidence(models.Model):
    """A file the auditor brings back from the client site."""

    _name = 'tuv.audit.evidence'
    _description = 'Audit Evidence'
    _order = 'project_id, category, id'

    project_id = fields.Many2one('project.project', required=True, ondelete='cascade', index=True)
    category = fields.Selection(EVIDENCE_CATEGORY, string='Category', required=True, default='other')
    name = fields.Char(string='Description', required=True)
    file = fields.Binary(string='File', attachment=True, required=True)
    file_name = fields.Char(string='File Name')
    checklist_line_id = fields.Many2one(
        'tuv.audit.checklist.line', string='Clause',
        domain="[('project_id', '=', project_id)]",
        help='The checklist clause this evidence supports, if any.')
    uploaded_by = fields.Many2one(
        'res.users', string='Uploaded By', default=lambda self: self.env.user, readonly=True)
    uploaded_on = fields.Datetime(string='Uploaded On', default=fields.Datetime.now, readonly=True)
    # The audit execution is to be uploaded the day of the audit: anything uploaded
    # after the day the audit was completed is flagged for the technical reviewer.
    uploaded_same_day = fields.Boolean(
        string='Same Day', compute='_compute_uploaded_same_day', store=True,
        help='Uploaded on or before the day the audit was completed.')

    @api.depends('uploaded_on', 'project_id.audit_completed_on')
    def _compute_uploaded_same_day(self):
        for evidence in self:
            completed = evidence.project_id.audit_completed_on
            evidence.uploaded_same_day = (not completed or not evidence.uploaded_on
                                          or evidence.uploaded_on.date() <= completed.date())

    # ------------------------------------------------------------------
    # The audit file is closed once the report is submitted
    # ------------------------------------------------------------------
    def _check_project_open(self, projects):
        user = self.env.user
        if self.env.su or user.has_group('tuv_austria_customization.group_planning_team') \
                or user.has_group('base.group_system'):
            return
        if any(p.audit_state == 'not_started' for p in projects):
            raise UserError(_('Start the audit before uploading its evidence.'))
        closed = projects.filtered(lambda p: p.report_state == 'submitted')
        if closed:
            raise UserError(_('The audit report of %s is submitted: its evidence can no longer '
                              'be changed. Ask the planning team.', ', '.join(closed.mapped('name'))))

    @api.model_create_multi
    def create(self, vals_list):
        projects = self.env['project.project'].browse({v.get('project_id') for v in vals_list})
        self._check_project_open(projects)
        records = super().create(vals_list)
        for project in records.project_id:
            added = records.filtered(lambda r: r.project_id == project)
            project.message_post(body=_('Audit evidence uploaded: %s', ', '.join(
                '%s (%s)' % (r.name, dict(EVIDENCE_CATEGORY)[r.category]) for r in added)))
        return records

    def write(self, vals):
        self._check_project_open(self.project_id)
        return super().write(vals)

    def unlink(self):
        self._check_project_open(self.project_id)
        return super().unlink()


class ProjectProject(models.Model):
    _inherit = 'project.project'

    audit_evidence_ids = fields.One2many('tuv.audit.evidence', 'project_id', string='Audit Evidence')
    audit_evidence_count = fields.Integer(compute='_compute_audit_evidence_count', string='Evidence')
    evidence_missing = fields.Char(compute='_compute_audit_evidence_count', string='Still Missing')
    evidence_late_count = fields.Integer(compute='_compute_audit_evidence_count',
                                         string='Uploaded After The Audit Day')

    @api.depends('audit_evidence_ids.category', 'audit_evidence_ids.uploaded_same_day')
    def _compute_audit_evidence_count(self):
        labels = dict(EVIDENCE_CATEGORY)
        for project in self:
            present = set(project.audit_evidence_ids.mapped('category'))
            project.audit_evidence_count = len(project.audit_evidence_ids)
            project.evidence_late_count = len(project.audit_evidence_ids.filtered(
                lambda e: not e.uploaded_same_day))
            project.evidence_missing = ', '.join(
                labels[c] for c in REQUIRED_CATEGORIES if c not in present) or False

    def action_attach_checklist_pdf(self):
        """Store the checklist Odoo prints as the Audit Checklist evidence."""
        self.ensure_one()
        if self.audit_state == 'not_started':
            raise UserError(_('Start the audit first: the checklist is created when it starts.'))
        pdf, _type = self.env['ir.actions.report']._render_qweb_pdf(
            'tuv_austria_customization.action_report_project_audit_checklist', self.ids)
        self.env['tuv.audit.evidence'].create({
            'project_id': self.id,
            'category': 'audit_checklist',
            'name': _('Audit Checklist (generated by Odoo)'),
            'file': base64.b64encode(pdf),
            'file_name': 'Audit Checklist - %s.pdf' % self.name,
        })
        return True

    def action_report_submit(self):
        for project in self:
            if project.evidence_missing:
                raise UserError(_('Upload the audit evidence before submitting the report. '
                                  'Still missing: %s.', project.evidence_missing))
        return super().action_report_submit()
