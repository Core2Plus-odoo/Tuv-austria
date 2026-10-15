import uuid

from odoo import _, api, fields, models

RATING = [
    ('1', 'Very Poor'),
    ('2', 'Poor'),
    ('3', 'Satisfactory'),
    ('4', 'Good'),
    ('5', 'Excellent'),
]
# The four things the client is asked about: (field, question on the form)
FEEDBACK_QUESTIONS = [
    ('rating_auditor', 'Auditor professionalism'),
    ('rating_audit_quality', 'Audit quality'),
    ('rating_report', 'Report clarity'),
    ('rating_service', 'Overall service experience'),
]
# The client's closing stage: entering it means the audit file is closed.
FEEDBACK_STAGE_NAMES = ('Feedback & Continuous Improvement',)


class ClientFeedback(models.Model):
    """The feedback a client gives once the audit is closed."""

    _name = 'tuv.client.feedback'
    _description = 'Client Feedback'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='/')
    project_id = fields.Many2one('project.project', string='Audit Project', required=True,
                                 readonly=True, ondelete='cascade', index=True)
    partner_id = fields.Many2one('res.partner', string='Client', required=True, readonly=True)
    auditor_id = fields.Many2one('res.partner', string='Lead Auditor', readonly=True)
    standards = fields.Char(string='Standard(s)', readonly=True)
    access_token = fields.Char(required=True, copy=False, readonly=True, index=True,
                               default=lambda self: uuid.uuid4().hex)
    state = fields.Selection([
        ('sent', 'Sent to Client'),
        ('answered', 'Answered'),
    ], string='Status', default='sent', required=True, tracking=True)
    sent_on = fields.Datetime(string='Sent On', readonly=True)
    answered_on = fields.Datetime(string='Answered On', readonly=True)

    rating_auditor = fields.Selection(RATING, string=FEEDBACK_QUESTIONS[0][1], readonly=True)
    rating_audit_quality = fields.Selection(RATING, string=FEEDBACK_QUESTIONS[1][1], readonly=True)
    rating_report = fields.Selection(RATING, string=FEEDBACK_QUESTIONS[2][1], readonly=True)
    rating_service = fields.Selection(RATING, string=FEEDBACK_QUESTIONS[3][1], readonly=True)
    comments = fields.Text(string='Client Comments', readonly=True)
    average_score = fields.Float(string='Average Score (out of 5)', compute='_compute_average_score',
                                 store=True, aggregator='avg', digits=(3, 2))
    feedback_url = fields.Char(string='Feedback Link', compute='_compute_feedback_url')

    _unique_token = models.UniqueIndex('(access_token)')

    @api.depends('rating_auditor', 'rating_audit_quality', 'rating_report', 'rating_service')
    def _compute_average_score(self):
        for fb in self:
            scores = [int(fb[field]) for field, _q in FEEDBACK_QUESTIONS if fb[field]]
            fb.average_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    def _compute_feedback_url(self):
        base = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for fb in self:
            fb.feedback_url = '%s/tuv/feedback/%s' % (base, fb.access_token)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('tuv.client.feedback') or '/'
        return super().create(vals_list)

    def _send_to_client(self):
        template = self.env.ref('tuv_austria_customization.mail_template_client_feedback')
        for fb in self:
            if not fb.partner_id.email:
                fb.project_id.message_post(body=_('Client feedback %s could not be e-mailed: the client has '
                                                  'no e-mail address. Link: %s', fb.name, fb.feedback_url))
                continue
            fb.message_post_with_source(template, partner_ids=fb.partner_id.ids,
                                        subtype_xmlid='mail.mt_comment', message_type='comment')
            fb.sent_on = fields.Datetime.now()

    def action_resend(self):
        self.filtered(lambda f: f.state == 'sent')._send_to_client()
        return True

    def _submit(self, answers, comments):
        """Store what the client filled in on the public form."""
        self.ensure_one()
        self.write(dict(answers, comments=comments, state='answered', answered_on=fields.Datetime.now()))
        body = _('Client feedback %(name)s received: average %(avg)s / 5 (%(detail)s).', name=self.name,
                 avg=self.average_score, detail=', '.join(
                     '%s %s' % (label, self[field]) for field, label in FEEDBACK_QUESTIONS))
        self.message_post(body=body)
        self.project_id.message_post(body=body)


class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    sends_client_feedback = fields.Boolean(
        string='Sends Client Feedback',
        help='Entering this stage closes the audit and e-mails the client the feedback form. '
             'Feedback & Continuous Improvement always does.')

    def _is_feedback_stage(self):
        self.ensure_one()
        return self.sends_client_feedback or self.name in FEEDBACK_STAGE_NAMES


class ProjectProject(models.Model):
    _inherit = 'project.project'

    feedback_ids = fields.One2many('tuv.client.feedback', 'project_id', string='Client Feedback')
    feedback_count = fields.Integer(compute='_compute_feedback_count')

    @api.depends('feedback_ids')
    def _compute_feedback_count(self):
        for project in self:
            project.feedback_count = len(project.feedback_ids)

    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' in vals:
            self.filtered(lambda p: p.stage_id and p.stage_id._is_feedback_stage())._trigger_client_feedback()
        return res

    def _trigger_client_feedback(self):
        """Audit closed: one feedback form per project, straight to the client."""
        Feedback = self.env['tuv.client.feedback'].sudo()
        for project in self.sudo():
            if project.feedback_ids or not project.partner_id:
                continue
            fb = Feedback.create({
                'project_id': project.id,
                'partner_id': project.partner_id.id,
                'auditor_id': project.auditor_id.id,
                'standards': project.atjf_standards,
            })
            fb._send_to_client()
            project.message_post(body=_('Audit closed: client feedback form %(name)s sent to %(client)s.',
                                        name=fb.name, client=project.partner_id.name))

    def action_view_feedback(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('tuv_austria_customization.action_tuv_client_feedback')
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {}
        if self.feedback_count == 1:
            action.update(views=[(False, 'form')], res_id=self.feedback_ids.id)
        return action
