from odoo import http
from odoo.http import request

from ..models.client_feedback import FEEDBACK_QUESTIONS, RATING


class ClientFeedbackController(http.Controller):
    """The public feedback form the client opens from the e-mail - no login needed."""

    def _feedback(self, token):
        # sudo: the client is not a user; the unguessable token is the access right
        return request.env['tuv.client.feedback'].sudo().search([('access_token', '=', token)], limit=1)

    @http.route('/tuv/feedback/<string:token>', type='http', auth='public', methods=['GET', 'POST'],
                csrf=True, sitemap=False)
    def feedback_form(self, token, **post):
        feedback = self._feedback(token)
        if not feedback:
            return request.not_found()
        values = {'feedback': feedback, 'questions': FEEDBACK_QUESTIONS, 'ratings': RATING,
                  'error': False, 'posted': post}
        if request.httprequest.method == 'POST' and feedback.state == 'sent':
            answers = {field: post.get(field) for field, _label in FEEDBACK_QUESTIONS}
            valid = {code for code, _label in RATING}
            if all(answers[field] in valid for field in answers):
                feedback._submit(answers, (post.get('comments') or '').strip()[:4000])
            else:
                values['error'] = True
        return request.render('tuv_austria_customization.client_feedback_page', values)
