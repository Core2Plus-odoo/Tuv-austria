from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .audit_document import _standard_key

# What the reviewer confirms, with the ISO/IEC 17021-1:2015 clause it comes from.
REVIEW_CHECKS = [
    ('chk_complete', 'The report is complete: every clause covered, summary, findings and '
                     'conclusion present (17021-1 9.4.8)'),
    ('chk_scope', 'Audit scope, EA code and standard match the application and the ATJF '
                  '(17021-1 9.1.2, 9.2.3)'),
    ('chk_team', 'The audit team was competent for the EA code and standard (17021-1 7.1, 9.2.2)'),
    ('chk_duration', 'The audit duration (man-days) is in line with IAF MD 5 (17021-1 9.1.4)'),
    ('chk_objective', 'Findings are objective, clear and supported by objective evidence '
                      '(17021-1 9.4.5)'),
    ('chk_nc_grading', 'Nonconformities are correctly graded (Major / Minor) and clearly stated '
                       '(17021-1 9.4.5)'),
    ('chk_evidence', 'Attendance sheet, audit checklist and reviewed documents are on file, '
                     'uploaded on the audit day (17021-1 9.4.8)'),
    ('chk_conclusion', 'The audit conclusion is consistent with the findings (17021-1 9.4.8, 9.5)'),
]


def reviewer_problems(project, user):
    """Why this user cannot review the report of this project ([] when he can)."""
    problems = []
    if not user.has_group('tuv_austria_customization.group_technical_reviewer'):
        problems.append(_('%s is not a Technical Reviewer', user.name))
        return problems
    partner = user.partner_id
    missing_ea = project.ea_code_ids - partner.approved_ea_code_ids
    if missing_ea:
        problems.append(_('not approved for EA code %s', ', '.join(missing_ea.mapped('name'))))
    competent = {_standard_key(s.name) for s in partner.certification_standard_ids}
    standards = [s.strip() for s in (project.atjf_standards or '').split(',') if s.strip()]
    missing_std = [s for s in standards if _standard_key(s) not in competent]
    if missing_std:
        problems.append(_('not competent in %s', ', '.join(missing_std)))
    # ISO/IEC 17021-1 9.5: reviewed by someone who was not involved in the audit
    if partner in project.audit_team_ids:
        problems.append(_('was a member of the audit team'))
    if project.report_submitted_by == user:
        problems.append(_('submitted the audit report'))
    return problems


class TechnicalReview(models.Model):
    """One technical review round of an audit report."""

    _name = 'tuv.technical.review'
    _description = 'Technical Review'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Review Number', required=True, copy=False, readonly=True, default='/')
    project_id = fields.Many2one('project.project', string='Project', required=True,
                                 ondelete='cascade', index=True, readonly=True)
    partner_id = fields.Many2one(related='project_id.partner_id', string='Client', store=True)
    reviewer_id = fields.Many2one('res.users', string='Technical Reviewer', required=True,
                                  readonly=True, tracking=True)
    state = fields.Selection([
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('returned', 'Returned to Auditor'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='in_review', required=True, tracking=True, copy=False)
    assigned_on = fields.Datetime(string='Assigned On', default=fields.Datetime.now, readonly=True)
    reviewed_on = fields.Datetime(string='Reviewed On', readonly=True, copy=False)

    # What is being reviewed, read from the project
    standards = fields.Char(related='project_id.atjf_standards', string='Standard(s)')
    ea_code_ids = fields.Many2many(related='project_id.ea_code_ids', string='EA Code')
    lead_auditor_id = fields.Many2one(related='project_id.auditor_id', string='Lead Auditor')
    audit_scope = fields.Text(related='project_id.audit_scope', string='Audited Scope')
    report_conclusion = fields.Selection(related='project_id.report_conclusion', string='Auditor\'s Conclusion')
    report_submitted_on = fields.Datetime(related='project_id.report_submitted_on')
    report_on_time = fields.Boolean(related='project_id.report_on_time', string='Report On Time')
    major_count = fields.Integer(related='project_id.audit_major_count', string='Major NC')
    minor_count = fields.Integer(related='project_id.audit_minor_count', string='Minor NC')
    observation_count = fields.Integer(related='project_id.audit_ofi_count', string='Observations')
    evidence_count = fields.Integer(related='project_id.audit_evidence_count', string='Evidence Files')
    evidence_late_count = fields.Integer(related='project_id.evidence_late_count',
                                         string='Evidence Uploaded After The Audit Day')

    chk_complete = fields.Boolean(string=REVIEW_CHECKS[0][1])
    chk_scope = fields.Boolean(string=REVIEW_CHECKS[1][1])
    chk_team = fields.Boolean(string=REVIEW_CHECKS[2][1])
    chk_duration = fields.Boolean(string=REVIEW_CHECKS[3][1])
    chk_objective = fields.Boolean(string=REVIEW_CHECKS[4][1])
    chk_nc_grading = fields.Boolean(string=REVIEW_CHECKS[5][1])
    chk_evidence = fields.Boolean(string=REVIEW_CHECKS[6][1])
    chk_conclusion = fields.Boolean(string=REVIEW_CHECKS[7][1])
    review_comments = fields.Text(string='Reviewer Comments')

    @api.constrains('reviewer_id', 'project_id')
    def _check_reviewer(self):
        for review in self:
            problems = reviewer_problems(review.project_id, review.reviewer_id)
            if problems:
                raise ValidationError(_('%(user)s cannot review %(project)s: %(why)s.',
                                        user=review.reviewer_id.name, project=review.project_id.name,
                                        why='; '.join(problems)))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('tuv.technical.review') or '/'
        reviews = super().create(vals_list)
        for review in reviews:
            review.message_subscribe(partner_ids=review.reviewer_id.partner_id.ids)
            review.activity_schedule(
                'mail.mail_activity_data_todo', user_id=review.reviewer_id.id,
                summary=_('Technical review of the audit report - %s', review.project_id.name))
        return reviews

    def _check_is_reviewer(self):
        user = self.env.user
        for review in self:
            if user != review.reviewer_id and not user.has_group('base.group_system'):
                raise UserError(_('Only %s, the assigned technical reviewer, can decide on %s.',
                                  review.reviewer_id.name, review.name))
            if review.state != 'in_review':
                raise UserError(_('%s is not in review.', review.name))

    def action_approve(self):
        self._check_is_reviewer()
        for review in self:
            unticked = [label for field, label in REVIEW_CHECKS if not review[field]]
            if unticked:
                raise UserError(_('Every point has to be confirmed to approve the report:\n- %s',
                                  '\n- '.join(unticked)))
            review.write({'state': 'approved', 'reviewed_on': fields.Datetime.now()})
            review.activity_feedback(['mail.mail_activity_data_todo'], feedback=_('Report approved.'))
            # sudo: a reviewer is a project user, who cannot write on the project
            review.project_id.sudo().message_post(body=_(
                'Technical review %(name)s: audit report APPROVED by %(user)s.',
                name=review.name, user=self.env.user.name))
        return True

    def action_return(self):
        self._check_is_reviewer()
        for review in self:
            if not review.review_comments:
                raise UserError(_('Write in the comments what the auditor has to correct.'))
            review.write({'state': 'returned', 'reviewed_on': fields.Datetime.now()})
            review.activity_feedback(['mail.mail_activity_data_todo'], feedback=_('Returned to the auditor.'))
            project = review.project_id.sudo()
            project.write({'report_state': 'draft'})
            project.message_post(body=_(
                'Technical review %(name)s: audit report RETURNED to the auditor by %(user)s: %(why)s',
                name=review.name, user=self.env.user.name, why=review.review_comments))
            project.activity_schedule(
                'mail.mail_activity_data_todo', user_id=(project.user_id or self.env.user).id,
                summary=_('Correct the audit report (technical review %s)', review.name),
                note=review.review_comments)
        return True


class ProjectProject(models.Model):
    _inherit = 'project.project'

    technical_reviewer_id = fields.Many2one(
        'res.users', string='Technical Reviewer', tracking=True,
        domain="[('id', 'in', technical_reviewer_candidate_ids)]",
        help='Only Technical Reviewers competent in every EA code and standard of the audit, '
             'and not involved in it, are offered.')
    technical_reviewer_candidate_ids = fields.Many2many(
        'res.users', compute='_compute_technical_reviewer_candidate_ids')
    technical_review_ids = fields.One2many('tuv.technical.review', 'project_id', string='Technical Reviews')
    technical_review_state = fields.Selection([
        ('none', 'Not Sent'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('returned', 'Returned to Auditor'),
    ], string='Technical Review', compute='_compute_technical_review_state')

    @api.depends('ea_code_ids', 'atjf_standards', 'audit_team_ids', 'report_submitted_by')
    def _compute_technical_reviewer_candidate_ids(self):
        group = self.env.ref('tuv_austria_customization.group_technical_reviewer')
        reviewers = self.env['res.users'].search([('all_group_ids', 'in', group.id)])
        for project in self:
            project.technical_reviewer_candidate_ids = reviewers.filtered(
                lambda u: not reviewer_problems(project, u))

    @api.depends('technical_review_ids.state')
    def _compute_technical_review_state(self):
        for project in self:
            # newest round by id: a round created in this transaction sits at the end of
            # the cached list, not at the front where _order would put it
            last = project.technical_review_ids.filtered(
                lambda r: r.state != 'cancelled').sorted('id')[-1:]
            project.technical_review_state = last.state if last else 'none'

    def action_send_to_technical_review(self):
        self.ensure_one()
        if self.report_state != 'submitted':
            raise UserError(_('Submit the audit report before sending it to technical review.'))
        if not self.technical_reviewer_id:
            raise UserError(_('Assign the Technical Reviewer first.'))
        if self.technical_review_state == 'in_review':
            raise UserError(_('The report is already in technical review.'))
        problems = reviewer_problems(self, self.technical_reviewer_id)
        if problems:
            raise UserError(_('%(user)s cannot review this report: %(why)s.',
                              user=self.technical_reviewer_id.name, why='; '.join(problems)))
        review = self.env['tuv.technical.review'].create({
            'project_id': self.id, 'reviewer_id': self.technical_reviewer_id.id})
        self.message_subscribe(partner_ids=self.technical_reviewer_id.partner_id.ids)
        self.message_post(body=_('Audit report sent to technical review %(name)s, reviewer %(user)s.',
                                 name=review.name, user=self.technical_reviewer_id.name))
        return self.action_view_technical_reviews()

    def action_report_reset(self):
        # the report being reworked, any review still running on it is void
        res = super().action_report_reset()
        self.technical_review_ids.filtered(lambda r: r.state == 'in_review').write({'state': 'cancelled'})
        return res

    def action_view_technical_reviews(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'tuv_austria_customization.action_tuv_technical_review')
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {}
        reviews = self.technical_review_ids
        if len(reviews) == 1:
            action.update(views=[(False, 'form')], res_id=reviews.id)
        return action
