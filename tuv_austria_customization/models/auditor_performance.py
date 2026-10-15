from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .client_feedback import RATING

ROLES = [('lead', 'Lead Auditor'), ('co', 'Co-Auditor'), ('trainee', 'Trainee')]
BANDS = [
    ('excellent', 'Excellent'),
    ('good', 'Good'),
    ('satisfactory', 'Satisfactory'),
    ('improve', 'Needs Improvement'),
]
# weight of each part of the job score; a part that does not apply is left out
WEIGHTS = {
    'client_auditor': 30,   # client's rating of the auditor's professionalism
    'client_overall': 10,   # client's average rating
    'report': 20,           # report submitted within 5 days (lead auditor)
    'review': 20,           # report approved by technical review first time (lead auditor)
    'evidence': 10,         # evidence uploaded on the audit day (lead auditor)
    'internal': 10,         # planning team's own evaluation
}


def score_band(score):
    if score >= 85:
        return 'excellent'
    if score >= 70:
        return 'good'
    if score >= 55:
        return 'satisfactory'
    return 'improve'


class AuditorPerformance(models.Model):
    """How one auditor performed on one job."""

    _name = 'tuv.auditor.performance'
    _description = 'Auditor Performance (per job)'
    _inherit = ['mail.thread']
    _order = 'closed_on desc, id desc'

    name = fields.Char(compute='_compute_name', store=True)
    project_id = fields.Many2one('project.project', string='Job', required=True, readonly=True,
                                 ondelete='cascade', index=True)
    auditor_id = fields.Many2one('res.partner', string='Auditor', required=True, readonly=True, index=True)
    role = fields.Selection(ROLES, string='Role', required=True, readonly=True)
    client_id = fields.Many2one(related='project_id.partner_id', string='Client', store=True)
    standards = fields.Char(string='Standard(s)', readonly=True)
    ea_codes = fields.Char(string='EA Code(s)', readonly=True)
    man_days = fields.Char(string='Man-days', readonly=True)
    audit_date = fields.Date(string='Audit Date', readonly=True)
    closed_on = fields.Date(string='Job Closed', readonly=True)
    year = fields.Char(string='Year', compute='_compute_year', store=True, index=True)

    # what Odoo already knows about the job - refreshed until the record is confirmed
    feedback_received = fields.Boolean(string='Client Feedback Received', readonly=True)
    client_rating_auditor = fields.Float(string='Client: Auditor Professionalism', readonly=True,
                                         digits=(3, 1), aggregator='avg')
    client_rating_overall = fields.Float(string='Client: Average Rating', readonly=True,
                                         digits=(3, 2), aggregator='avg')
    report_submitted = fields.Boolean(string='Report Submitted', readonly=True)
    report_on_time = fields.Boolean(string='Report Within 5 Days', readonly=True)
    report_days_late = fields.Integer(string='Report Days Late', readonly=True)
    review_rounds = fields.Integer(string='Technical Review Rounds', readonly=True)
    review_returns = fields.Integer(string='Returned By Technical Review', readonly=True)
    evidence_total = fields.Integer(string='Evidence Files', readonly=True)
    evidence_late = fields.Integer(string='Evidence After The Audit Day', readonly=True)
    major_nc = fields.Integer(string='Major NCs Raised', readonly=True)
    minor_nc = fields.Integer(string='Minor NCs Raised', readonly=True)

    internal_rating = fields.Selection(RATING, string='Planning Team Evaluation',
                                       help='Conduct, technical competence and cooperation, as seen by planning.')
    internal_remarks = fields.Text(string='Evaluation Remarks')

    job_score = fields.Float(string='Job Score (out of 100)', compute='_compute_job_score', store=True,
                             digits=(5, 1), aggregator='avg')
    band = fields.Selection(BANDS, string='Performance', compute='_compute_job_score', store=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], string='Status',
                             default='draft', required=True, tracking=True)
    confirmed_by = fields.Many2one('res.users', readonly=True)
    confirmed_on = fields.Datetime(readonly=True)

    _one_per_role = models.UniqueIndex('(project_id, auditor_id, role)')

    @api.depends('project_id', 'auditor_id', 'role')
    def _compute_name(self):
        roles = dict(ROLES)
        for rec in self:
            rec.name = '%s - %s (%s)' % (rec.project_id.name or '', rec.auditor_id.name or '', roles.get(rec.role, ''))

    @api.depends('closed_on')
    def _compute_year(self):
        for rec in self:
            rec.year = str(rec.closed_on.year) if rec.closed_on else False

    def _score_parts(self):
        """(weight key, value 0-100) of every part that applies to this record."""
        self.ensure_one()
        parts = []
        if self.feedback_received:
            parts.append(('client_auditor', self.client_rating_auditor * 20))
            parts.append(('client_overall', self.client_rating_overall * 20))
        if self.role == 'lead':
            if self.report_submitted:
                parts.append(('report', 100 if self.report_on_time else max(0, 100 - 10 * self.report_days_late)))
            if self.review_rounds:
                parts.append(('review', max(0, 100 - 40 * self.review_returns)))
            if self.evidence_total:
                parts.append(('evidence', (self.evidence_total - self.evidence_late) * 100.0 / self.evidence_total))
        if self.internal_rating:
            parts.append(('internal', int(self.internal_rating) * 20))
        return parts

    @api.depends('feedback_received', 'client_rating_auditor', 'client_rating_overall', 'role',
                 'report_submitted', 'report_on_time', 'report_days_late', 'review_rounds', 'review_returns',
                 'evidence_total', 'evidence_late', 'internal_rating')
    def _compute_job_score(self):
        for rec in self:
            parts = rec._score_parts()
            weight = sum(WEIGHTS[key] for key, _v in parts)
            rec.job_score = round(sum(WEIGHTS[key] * value for key, value in parts) / weight, 1) if weight else 0.0
            rec.band = score_band(rec.job_score) if weight else False

    def _refresh_metrics(self):
        """Read the job again - feedback, report, review and evidence may have moved on."""
        for rec in self.filtered(lambda r: r.state == 'draft'):
            project = rec.project_id
            fb = project.feedback_ids.filtered(lambda f: f.state == 'answered')[:1]
            reviews = project.technical_review_ids.filtered(lambda r: r.state in ('approved', 'returned'))
            vals = {
                'feedback_received': bool(fb),
                'client_rating_auditor': int(fb.rating_auditor) if fb.rating_auditor else 0.0,
                'client_rating_overall': fb.average_score if fb else 0.0,
                'major_nc': len(project.nonconformity_ids.filtered(lambda n: n.grade == 'major_nc')),
                'minor_nc': len(project.nonconformity_ids.filtered(lambda n: n.grade == 'minor_nc')),
            }
            if rec.role == 'lead':
                vals.update({
                    'report_submitted': project.report_state == 'submitted',
                    'report_on_time': project.report_on_time,
                    'report_days_late': project.report_days_late,
                    'review_rounds': len(reviews),
                    'review_returns': len(reviews.filtered(lambda r: r.state == 'returned')),
                    'evidence_total': project.audit_evidence_count,
                    'evidence_late': project.evidence_late_count,
                })
            rec.write(vals)

    def action_refresh(self):
        self._refresh_metrics()
        return True

    def action_confirm(self):
        user = self.env.user
        if not (user.has_group('tuv_austria_customization.group_planning_team') or user.has_group('base.group_system')):
            raise UserError(_('Only the planning team can confirm auditor performance.'))
        for rec in self:
            rec._refresh_metrics()
            if not rec.internal_rating:
                raise UserError(_('%s: give the planning team evaluation first.', rec.name))
            rec.write({'state': 'confirmed', 'confirmed_by': user.id, 'confirmed_on': fields.Datetime.now()})
        return True

    def action_reset(self):
        if not self.env.user.has_group('base.group_system'):
            raise UserError(_('Only an administrator can reopen a confirmed performance record.'))
        self.write({'state': 'draft'})
        return True


class AuditorReview(models.Model):
    """The annual performance review and competence re-evaluation of one auditor."""

    _name = 'tuv.auditor.review'
    _description = 'Annual Auditor Performance Review'
    _inherit = ['mail.thread']
    _order = 'year desc, auditor_id'

    name = fields.Char(compute='_compute_name', store=True)
    auditor_id = fields.Many2one('res.partner', string='Auditor', required=True, readonly=True, index=True)
    year = fields.Char(string='Year', required=True, readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')], string='Status',
                             default='draft', required=True, tracking=True)

    # the year in figures - refreshed until the review is approved
    jobs_count = fields.Integer(string='Jobs (confirmed)', readonly=True)
    unconfirmed_count = fields.Integer(string='Jobs Not Yet Confirmed', readonly=True)
    avg_job_score = fields.Float(string='Average Job Score', readonly=True, digits=(5, 1))
    avg_client_rating = fields.Float(string='Average Client Rating (auditor)', readonly=True, digits=(3, 2))
    reports_on_time_pct = fields.Float(string='% Reports Within 5 Days', readonly=True, digits=(5, 1))
    first_pass_review_pct = fields.Float(string='% Approved By Technical Review First Time', readonly=True, digits=(5, 1))
    evidence_on_time_pct = fields.Float(string='% Evidence On The Audit Day', readonly=True, digits=(5, 1))
    major_nc = fields.Integer(string='Major NCs Raised', readonly=True)
    minor_nc = fields.Integer(string='Minor NCs Raised', readonly=True)
    band = fields.Selection(BANDS, string='Overall Performance', readonly=True)
    performance_ids = fields.Many2many('tuv.auditor.performance', string='Jobs Of The Year',
                                       compute='_compute_performance_ids')

    # evaluation and competence re-evaluation
    strengths = fields.Text(string='Strengths')
    improvements = fields.Text(string='Areas For Improvement')
    training_required = fields.Text(string='Training / Actions Required')
    decision = fields.Selection([
        ('maintain', 'Competence Maintained'),
        ('maintain_actions', 'Maintained With Actions'),
        ('restrict', 'Scope Restricted'),
        ('suspend', 'Suspended'),
    ], string='Competence Re-evaluation', tracking=True)
    proposed_ea_code_ids = fields.Many2many('industry.ea.code', 'tuv_auditor_review_ea_rel', 'review_id', 'ea_id',
                                            string='Approved EA Codes (after review)')
    proposed_standard_ids = fields.Many2many('certification.standard', 'tuv_auditor_review_std_rel', 'review_id',
                                             'standard_id', string='Standards Competent In (after review)')
    proposed_lead_auditor = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Lead Auditor (after review)')
    approved_by = fields.Many2one('res.users', readonly=True)
    approved_on = fields.Datetime(readonly=True)

    _one_per_year = models.UniqueIndex('(auditor_id, year)', 'This auditor already has a review for that year.')

    @api.depends('auditor_id', 'year')
    def _compute_name(self):
        for rev in self:
            rev.name = '%s - %s' % (rev.year or '', rev.auditor_id.name or '')

    def _compute_performance_ids(self):
        Perf = self.env['tuv.auditor.performance']
        for rev in self:
            rev.performance_ids = Perf.search([('auditor_id', '=', rev.auditor_id.id), ('year', '=', rev.year)])

    @api.model_create_multi
    def create(self, vals_list):
        reviews = super().create(vals_list)
        for rev in reviews:
            auditor = rev.auditor_id
            rev.write({'proposed_ea_code_ids': [(6, 0, auditor.approved_ea_code_ids.ids)],
                       'proposed_standard_ids': [(6, 0, auditor.certification_standard_ids.ids)],
                       'proposed_lead_auditor': auditor.lead_auditor})
        reviews._refresh_figures()
        return reviews

    def _refresh_figures(self):
        Perf = self.env['tuv.auditor.performance']
        for rev in self.filtered(lambda r: r.state == 'draft'):
            year_recs = Perf.search([('auditor_id', '=', rev.auditor_id.id), ('year', '=', rev.year)])
            jobs = year_recs.filtered(lambda r: r.state == 'confirmed')
            lead = jobs.filtered(lambda r: r.role == 'lead')
            with_fb = jobs.filtered('feedback_received')

            def pct(records, test):
                return round(len(records.filtered(test)) * 100.0 / len(records), 1) if records else 0.0

            avg = round(sum(jobs.mapped('job_score')) / len(jobs), 1) if jobs else 0.0
            rev.write({
                'jobs_count': len(jobs),
                'unconfirmed_count': len(year_recs - jobs),
                'avg_job_score': avg,
                'avg_client_rating': round(sum(with_fb.mapped('client_rating_auditor')) / len(with_fb), 2) if with_fb else 0.0,
                'reports_on_time_pct': pct(lead.filtered('report_submitted'), lambda r: r.report_on_time),
                'first_pass_review_pct': pct(lead.filtered('review_rounds'), lambda r: not r.review_returns),
                'evidence_on_time_pct': pct(lead.filtered('evidence_total'), lambda r: not r.evidence_late),
                'major_nc': sum(jobs.mapped('major_nc')),
                'minor_nc': sum(jobs.mapped('minor_nc')),
                'band': score_band(avg) if jobs else False,
            })

    def action_refresh(self):
        self._refresh_figures()
        return True

    def action_approve(self):
        user = self.env.user
        if not (user.has_group('tuv_austria_customization.group_planning_team') or user.has_group('base.group_system')):
            raise UserError(_('Only the planning team can approve an auditor review.'))
        for rev in self:
            rev._refresh_figures()
            if not rev.jobs_count:
                raise UserError(_('%s: no confirmed job in %s to review.', rev.auditor_id.name, rev.year))
            if not rev.decision:
                raise UserError(_('%s: choose the competence re-evaluation decision.', rev.name))
            if rev.decision in ('maintain_actions', 'restrict', 'suspend') and not rev.training_required:
                raise UserError(_('%s: write the training / actions required for this decision.', rev.name))
            # the auditor database used to assign audits takes the outcome
            auditor_vals = {
                'approved_ea_code_ids': [(6, 0, rev.proposed_ea_code_ids.ids)],
                'certification_standard_ids': [(6, 0, rev.proposed_standard_ids.ids)],
                'lead_auditor': rev.proposed_lead_auditor,
            }
            if rev.decision == 'suspend':
                auditor_vals['auditor_active'] = 'no'
            rev.auditor_id.sudo().write(auditor_vals)
            rev.write({'state': 'approved', 'approved_by': user.id, 'approved_on': fields.Datetime.now()})
            decision = dict(rev._fields['decision'].selection)[rev.decision]
            body = _('Annual performance review %(year)s approved: %(decision)s (average job score %(score)s, %(jobs)s '
                     'job(s)). Approved EA codes: %(ea)s; standards: %(std)s; lead auditor: %(lead)s.',
                     year=rev.year, decision=decision, score=rev.avg_job_score, jobs=rev.jobs_count,
                     ea=', '.join(n.strip() for n in rev.proposed_ea_code_ids.mapped('name')) or '-',
                     std=', '.join(n.strip() for n in rev.proposed_standard_ids.mapped('name')) or '-',
                     lead=rev.proposed_lead_auditor or '-')
            rev.message_post(body=body)
            rev.auditor_id.message_post(body=body)
        return True

    @api.model
    def _generate_for_year(self, year):
        """A draft review for every auditor who worked on a job closed that year."""
        year = str(year)
        auditors = self.env['tuv.auditor.performance'].search([('year', '=', year)]).auditor_id
        existing = self.search([('year', '=', year)]).auditor_id
        return self.create([{'auditor_id': a.id, 'year': year} for a in auditors - existing])

    def action_open_generate(self):
        return self.env['ir.actions.actions']._for_xml_id(
            'tuv_austria_customization.action_tuv_auditor_review_generate')

    @api.model
    def _cron_generate_previous_year(self):
        return len(self._generate_for_year(fields.Date.context_today(self).year - 1))


class AuditorReviewGenerate(models.TransientModel):
    _name = 'tuv.auditor.review.generate'
    _description = 'Generate Annual Auditor Reviews'

    year = fields.Char(string='Year', required=True,
                       default=lambda self: str(fields.Date.context_today(self).year))

    def action_generate(self):
        reviews = self.env['tuv.auditor.review']._generate_for_year(self.year)
        return {
            'type': 'ir.actions.act_window', 'name': _('Annual Reviews %s', self.year),
            'res_model': 'tuv.auditor.review', 'view_mode': 'list,form',
            'domain': [('year', '=', self.year)], 'context': {'created': len(reviews)},
        }


class ResPartner(models.Model):
    _inherit = 'res.partner'

    performance_ids = fields.One2many('tuv.auditor.performance', 'auditor_id', string='Job Performance')
    auditor_review_ids = fields.One2many('tuv.auditor.review', 'auditor_id', string='Annual Reviews')
    performance_count = fields.Integer(compute='_compute_performance_count')
    performance_avg_score = fields.Float(compute='_compute_performance_count', string='Average Job Score')

    @api.depends('performance_ids.job_score')
    def _compute_performance_count(self):
        for partner in self:
            recs = partner.performance_ids
            partner.performance_count = len(recs)
            partner.performance_avg_score = round(sum(recs.mapped('job_score')) / len(recs), 1) if recs else 0.0

    def action_view_performance(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('tuv_austria_customization.action_tuv_auditor_performance')
        action['domain'] = [('auditor_id', '=', self.id)]
        action['context'] = {}
        return action

    def action_view_auditor_reviews(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('tuv_austria_customization.action_tuv_auditor_review')
        action['domain'] = [('auditor_id', '=', self.id)]
        action['context'] = {}
        return action


class ProjectProject(models.Model):
    _inherit = 'project.project'

    performance_ids = fields.One2many('tuv.auditor.performance', 'project_id', string='Auditor Performance')

    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' in vals:
            self.filtered(lambda p: p.stage_id and p.stage_id._is_feedback_stage())._create_auditor_performance()
        return res

    def _create_auditor_performance(self):
        """Job closed: one performance record per member of the audit team."""
        Perf = self.env['tuv.auditor.performance'].sudo()
        for project in self.sudo():
            team = [('lead', project.auditor_id), ('co', project.md_co_auditor_id), ('trainee', project.md_trainee_id)]
            created = Perf.browse()
            for role, auditor in team:
                if not auditor or project.performance_ids.filtered(
                        lambda r: r.auditor_id == auditor and r.role == role):
                    continue
                created |= Perf.create({
                    'project_id': project.id, 'auditor_id': auditor.id, 'role': role,
                    'standards': project.atjf_standards,
                    'ea_codes': ', '.join(n.strip() for n in project.ea_code_ids.mapped('name')),
                    'man_days': project.md_audit_duration,
                    'audit_date': project.md_audit_date_st2 or project.md_audit_date_st1,
                    'closed_on': fields.Date.context_today(project),
                })
            created._refresh_metrics()
            if created:
                project.message_post(body=_('Auditor performance recorded for %s.', ', '.join(created.mapped('name'))))

    def action_view_auditor_performance(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('tuv_austria_customization.action_tuv_auditor_performance')
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {}
        return action


class ClientFeedback(models.Model):
    _inherit = 'tuv.client.feedback'

    def _submit(self, answers, comments):
        res = super()._submit(answers, comments)
        # the client's ratings land on the auditors' job records straight away
        self.project_id.performance_ids.sudo()._refresh_metrics()
        return res
