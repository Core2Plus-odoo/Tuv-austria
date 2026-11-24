from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .search_utils import boolean_search_positive

# Feedback below this average, or any single rating at or below LOW_RATING, needs attention.
LOW_AVERAGE = 3.0
LOW_RATING = 2
REVIEW_DAYS = 5


def check_certification_manager(env):
    user = env.user
    if not (user.has_group('tuv_austria_customization.group_certification_manager')
            or user.has_group('base.group_system')):
        raise UserError(_('Only the Certification Manager can do this.'))


class ClientFeedback(models.Model):
    _inherit = 'tuv.client.feedback'

    state = fields.Selection(selection_add=[('reviewed', 'Reviewed')], ondelete={'reviewed': 'set default'})
    needs_attention = fields.Boolean(string='Needs Attention', compute='_compute_needs_attention', store=True,
                                     help='Average below 3 or any rating "Poor" or worse.')
    review_notes = fields.Text(string='Certification Manager Analysis')
    review_outcome = fields.Selection([
        ('no_action', 'No Action Needed'),
        ('actions', 'Actions Required'),
    ], string='Review Outcome', tracking=True)
    reviewed_by = fields.Many2one('res.users', string='Reviewed By', readonly=True, copy=False)
    reviewed_on = fields.Datetime(string='Reviewed On', readonly=True, copy=False)
    action_ids = fields.One2many('tuv.improvement.action', 'feedback_id', string='Actions')
    action_count = fields.Integer(compute='_compute_action_count')

    @api.depends('state', 'average_score', 'rating_auditor', 'rating_audit_quality', 'rating_report', 'rating_service')
    def _compute_needs_attention(self):
        for fb in self:
            ratings = [int(r) for r in (fb.rating_auditor, fb.rating_audit_quality, fb.rating_report,
                                        fb.rating_service) if r]
            fb.needs_attention = bool(ratings) and (fb.average_score < LOW_AVERAGE or min(ratings) <= LOW_RATING)

    @api.depends('action_ids')
    def _compute_action_count(self):
        for fb in self:
            fb.action_count = len(fb.action_ids)

    def _submit(self, answers, comments):
        res = super()._submit(answers, comments)
        # straight onto the Certification Manager's desk
        group = self.env.ref('tuv_austria_customization.group_certification_manager')
        managers = self.env['res.users'].sudo().search([('all_group_ids', 'in', group.id)])
        for fb in self:
            summary = (_('LOW FEEDBACK - review %(name)s (average %(avg)s)', name=fb.name, avg=fb.average_score)
                       if fb.needs_attention else _('Review client feedback %s', fb.name))
            for user in managers or self.env.user:
                fb.activity_schedule('mail.mail_activity_data_todo', user_id=user.id, summary=summary,
                                     date_deadline=fields.Date.context_today(fb) + timedelta(days=REVIEW_DAYS))
        return res

    def action_create_improvement_action(self):
        self.ensure_one()
        check_certification_manager(self.env)
        return {
            'type': 'ir.actions.act_window', 'name': _('New Action'), 'res_model': 'tuv.improvement.action',
            'view_mode': 'form', 'target': 'current',
            'context': {
                'default_source': 'client_feedback', 'default_feedback_id': self.id,
                'default_project_id': self.project_id.id, 'default_partner_id': self.partner_id.id,
                'default_auditor_id': self.auditor_id.id,
                'default_action_type': 'corrective' if self.needs_attention else 'improvement',
                'default_description': self.comments or False,
            },
        }

    def action_complete_review(self):
        check_certification_manager(self.env)
        for fb in self:
            if fb.state != 'answered':
                raise UserError(_('%s has not been answered by the client yet.', fb.name))
            if not fb.review_notes or not fb.review_outcome:
                raise UserError(_('%s: write the analysis and choose the outcome.', fb.name))
            if fb.review_outcome == 'no_action' and fb.needs_attention:
                raise UserError(_('%s is low feedback: it needs at least one corrective or improvement action.',
                                  fb.name))
            if fb.review_outcome == 'actions' and not fb.action_ids:
                raise UserError(_('%s: create the corrective / improvement action(s) first.', fb.name))
            fb.write({'state': 'reviewed', 'reviewed_by': self.env.user.id, 'reviewed_on': fields.Datetime.now()})
            fb.activity_feedback(['mail.mail_activity_data_todo'], feedback=_('Feedback reviewed.'))
            fb.message_post(body=_('Reviewed by the Certification Manager: %(outcome)s.%(actions)s',
                                   outcome=dict(fb._fields['review_outcome'].selection)[fb.review_outcome],
                                   actions=(' ' + ', '.join(fb.action_ids.mapped('name'))) if fb.action_ids else ''))
        return True

    def action_view_actions(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('tuv_austria_customization.action_tuv_improvement_action')
        action['domain'] = [('feedback_id', '=', self.id)]
        action['context'] = {}
        return action


class ImprovementAction(models.Model):
    """A corrective or improvement action, followed until its effectiveness is verified."""

    _name = 'tuv.improvement.action'
    _description = 'Corrective / Improvement Action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date, id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='/')
    action_type = fields.Selection([
        ('corrective', 'Corrective Action'),
        ('improvement', 'Improvement Action'),
    ], string='Type', required=True, default='improvement', tracking=True)
    source = fields.Selection([
        ('client_feedback', 'Client Feedback'),
        ('auditor_performance', 'Auditor Performance'),
        ('other', 'Other'),
    ], string='Source', required=True, default='client_feedback')
    feedback_id = fields.Many2one('tuv.client.feedback', string='Client Feedback', ondelete='set null', index=True)
    project_id = fields.Many2one('project.project', string='Audit Project', ondelete='set null')
    partner_id = fields.Many2one('res.partner', string='Client')
    auditor_id = fields.Many2one('res.partner', string='Auditor Concerned', domain="[('contact_type', '=', 'auditor')]")

    description = fields.Text(string='Issue / Opportunity', required=True)
    root_cause = fields.Text(string='Root Cause')
    action_plan = fields.Text(string='Action To Take', required=True)
    responsible_id = fields.Many2one('res.users', string='Responsible', required=True, tracking=True)
    due_date = fields.Date(string='Due Date', required=True, tracking=True)

    state = fields.Selection([
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('done', 'Implemented'),
        ('verified', 'Verified Effective'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='open', required=True, tracking=True)
    completion_note = fields.Text(string='What Was Done')
    completed_on = fields.Date(string='Implemented On', readonly=True)
    verification_note = fields.Text(string='Effectiveness Verification')
    verified_by = fields.Many2one('res.users', string='Verified By', readonly=True)
    verified_on = fields.Date(string='Verified On', readonly=True)
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_is_overdue', search='_search_is_overdue')
    overdue_notified = fields.Boolean(copy=False)

    @api.depends('state', 'due_date')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for action in self:
            action.is_overdue = action.state in ('open', 'in_progress') and bool(action.due_date) and action.due_date < today

    def _search_is_overdue(self, operator, value):
        domain = [('state', 'in', ('open', 'in_progress')), ('due_date', '<', fields.Date.context_today(self))]
        return domain if boolean_search_positive(operator, value) else ['!', '&'] + domain

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                code = 'tuv.corrective.action' if vals.get('action_type') == 'corrective' else 'tuv.improvement.action'
                vals['name'] = self.env['ir.sequence'].next_by_code(code) or '/'
        actions = super().create(vals_list)
        for action in actions:
            if action.action_type == 'corrective' and not action.root_cause:
                raise UserError(_('A corrective action needs its root cause.'))
            action.activity_schedule('mail.mail_activity_data_todo', user_id=action.responsible_id.id,
                                     date_deadline=action.due_date, summary=_('%(name)s: %(plan)s', name=action.name,
                                                                              plan=(action.action_plan or '')[:80]))
            if action.feedback_id:
                action.feedback_id.message_post(body=_('%(type)s %(name)s created, responsible %(user)s, due %(due)s.',
                                                       type=dict(action._fields['action_type'].selection)[action.action_type],
                                                       name=action.name, user=action.responsible_id.name, due=action.due_date))
        return actions

    def action_start(self):
        self.filtered(lambda a: a.state == 'open').write({'state': 'in_progress'})
        return True

    def action_mark_done(self):
        for action in self:
            if action.state not in ('open', 'in_progress'):
                raise UserError(_('%s is not open.', action.name))
            if not action.completion_note:
                raise UserError(_('%s: describe what was done.', action.name))
            action.write({'state': 'done', 'completed_on': fields.Date.context_today(action)})
            action.activity_feedback(['mail.mail_activity_data_todo'], feedback=_('Implemented.'))
            group = self.env.ref('tuv_austria_customization.group_certification_manager')
            for user in self.env['res.users'].search([('all_group_ids', 'in', group.id)]) or self.env.user:
                action.activity_schedule('mail.mail_activity_data_todo', user_id=user.id,
                                         summary=_('Verify effectiveness of %s', action.name))
        return True

    def action_verify(self):
        check_certification_manager(self.env)
        for action in self:
            if action.state != 'done':
                raise UserError(_('%s has to be implemented before it can be verified.', action.name))
            if not action.verification_note:
                raise UserError(_('%s: write how the effectiveness was verified.', action.name))
            if action.responsible_id == self.env.user:
                raise UserError(_('%s: the person responsible cannot verify their own action.', action.name))
            action.write({'state': 'verified', 'verified_by': self.env.user.id,
                          'verified_on': fields.Date.context_today(action)})
            action.activity_feedback(['mail.mail_activity_data_todo'], feedback=_('Verified effective.'))
        return True

    def action_reopen(self):
        """Not effective: back to work."""
        check_certification_manager(self.env)
        for action in self.filtered(lambda a: a.state == 'done'):
            if not action.verification_note:
                raise UserError(_('%s: write in the verification why it is not effective.', action.name))
            action.write({'state': 'in_progress'})
            action.message_post(body=_('Not effective: %s', action.verification_note))
            action.activity_schedule('mail.mail_activity_data_todo', user_id=action.responsible_id.id,
                                     date_deadline=action.due_date, summary=_('%s reopened - not effective', action.name))
        return True

    def action_cancel(self):
        check_certification_manager(self.env)
        self.write({'state': 'cancelled'})
        self.activity_unlink(['mail.mail_activity_data_todo'])
        return True

    @api.model
    def _cron_flag_overdue(self):
        overdue = self.search([('is_overdue', '=', True), ('overdue_notified', '=', False)])
        for action in overdue:
            action.message_post(body=_('Overdue: the action was due on %s.', action.due_date))
            action.activity_schedule('mail.mail_activity_data_todo', user_id=action.responsible_id.id,
                                     summary=_('OVERDUE %s', action.name))
        overdue.write({'overdue_notified': True})
        return len(overdue)
