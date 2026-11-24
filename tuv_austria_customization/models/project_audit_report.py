from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

# The auditor has this many days after the audit is completed to submit the report.
REPORT_DAYS = 5
FINDING_RESULTS = ('major_nc', 'minor_nc', 'ofi')


class ProjectProject(models.Model):
    """The audit report the auditor submits after the audit.

    Findings are not typed in again: the Major / Minor nonconformities and the
    observations are the checklist lines the auditor already marked on site.
    """

    _inherit = 'project.project'

    report_state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
    ], string='Report Status', default='draft', required=True, copy=False, tracking=True)
    report_due_date = fields.Date(
        string='Report Due', compute='_compute_report_due_date', store=True,
        help='%s days after the audit was completed.' % REPORT_DAYS)
    report_submitted_on = fields.Datetime(string='Submitted On', readonly=True, copy=False)
    report_submitted_by = fields.Many2one('res.users', string='Submitted By', readonly=True, copy=False)
    report_on_time = fields.Boolean(string='Submitted On Time', readonly=True, copy=False)
    report_days_late = fields.Integer(string='Days Late', readonly=True, copy=False)
    report_late_reason = fields.Text(string='Reason For Late Submission', copy=False)

    report_summary = fields.Html(string='Audit Summary', copy=False)
    report_findings = fields.Html(string='Findings', copy=False)
    report_conclusion = fields.Selection([
        ('recommend', 'Recommend Certification'),
        ('not_recommend', 'Do Not Recommend Certification'),
    ], string='Audit Conclusion', copy=False, tracking=True)
    report_conclusion_note = fields.Text(string='Conclusion Justification', copy=False)

    # The nonconformities and observations of the checklist, for the report.
    audit_finding_line_ids = fields.One2many(
        'tuv.audit.checklist.line', 'project_id', string='Nonconformities & Observations',
        domain=[('result', 'in', FINDING_RESULTS)], readonly=True)

    @api.depends('audit_completed_on')
    def _compute_report_due_date(self):
        for project in self:
            completed = project.audit_completed_on
            project.report_due_date = (completed.date() + timedelta(days=REPORT_DAYS)
                                       if completed else False)

    # ------------------------------------------------------------------
    # Audit completed -> the report clock starts
    # ------------------------------------------------------------------
    def action_audit_complete(self):
        res = super().action_audit_complete()
        for project in self:
            project.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=project.report_due_date,
                user_id=(project.user_id or self.env.user).id,
                summary=_('Submit audit report - %s', project.name),
                note=_('The audit was completed on %(done)s; the report is due by %(due)s.',
                       done=fields.Date.to_string(project.audit_completed_on.date()),
                       due=fields.Date.to_string(project.report_due_date)))
        return res

    def action_audit_reopen(self):
        # a reopened audit can change the findings, so its report is redone
        res = super().action_audit_reopen()
        submitted = self.filtered(lambda p: p.report_state == 'submitted')
        if submitted:
            submitted.write({'report_state': 'draft'})
            for project in submitted:
                project.message_post(body=_('Audit report back to draft: the audit was reopened.'))
        return res

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------
    def action_report_submit(self):
        self.ensure_one()
        if self.audit_state != 'done':
            raise UserError(_('Complete the audit before submitting its report.'))
        if self.report_state == 'submitted':
            raise UserError(_('The audit report of %s is already submitted.', self.name))
        missing = []
        if not self._html_has_text(self.report_summary):
            missing.append(_('Audit Summary'))
        if not self.report_conclusion:
            missing.append(_('Audit Conclusion'))
        if missing:
            raise UserError(_('Fill these in before submitting the report:\n- %s', '\n- '.join(missing)))
        if (self.report_conclusion == 'recommend' and self.audit_major_count
                and not self.report_conclusion_note):
            raise UserError(_('The audit has %s major nonconformity(ies). Write the justification '
                              'for recommending certification anyway.', self.audit_major_count))
        today = fields.Date.context_today(self)
        days_late = max((today - self.report_due_date).days, 0) if self.report_due_date else 0
        if days_late and not self.report_late_reason:
            raise UserError(_('The report was due on %(due)s (%(days)s day(s) ago). Write the reason '
                              'for the late submission.', due=self.report_due_date, days=days_late))
        self.write({
            'report_state': 'submitted',
            'report_submitted_on': fields.Datetime.now(),
            'report_submitted_by': self.env.user.id,
            'report_on_time': not days_late,
            'report_days_late': days_late,
        })
        self.activity_feedback(['mail.mail_activity_data_todo'],
                               feedback=_('Audit report submitted.'))
        conclusion = dict(self._fields['report_conclusion'].selection)[self.report_conclusion]
        self.message_post(body=_(
            'Audit report submitted by %(user)s %(timing)s: %(conclusion)s '
            '(%(major)s major NC, %(minor)s minor NC, %(obs)s observation(s)).',
            user=self.env.user.name,
            timing=_('on time') if not days_late else _('%s day(s) late', days_late),
            conclusion=conclusion, major=self.audit_major_count,
            minor=self.audit_minor_count, obs=self.audit_ofi_count))
        return True

    def action_report_reset(self):
        self.ensure_one()
        self.write({'report_state': 'draft'})
        self.message_post(body=_('Audit report sent back to draft by %s.', self.env.user.name))
        return True

    @api.model
    def _html_has_text(self, html):
        return bool(html2plaintext(html or '').strip())
