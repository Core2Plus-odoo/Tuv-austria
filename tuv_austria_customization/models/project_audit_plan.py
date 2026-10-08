from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date


class ProjectProject(models.Model):
    """The audit plan the client receives once the ATJF is reviewed.

    Approving the ATJF is the moment the audit dates and the team are confirmed, so
    that is when the client is told: the confirmed dates, who audits them and the
    documents to have ready. It can be sent again by hand after a change.
    """

    _inherit = 'project.project'

    # Filled from the master list by the standards of the audit, then editable: the
    # planning team adds or drops a document for this client.
    audit_document_ids = fields.Many2many(
        'tuv.audit.document', 'project_audit_document_rel', 'project_id', 'document_id',
        string='Documents To Prepare', compute='_compute_audit_document_ids',
        store=True, readonly=False)
    audit_plan_sent_on = fields.Datetime(string='Audit Plan Sent On', readonly=True, copy=False)

    @api.depends('certification_standard', 'md_standard_1', 'md_standard_2',
                 'md_standard_3', 'md_standard_other')
    def _compute_audit_document_ids(self):
        Document = self.env['tuv.audit.document']
        for project in self:
            project.audit_document_ids = Document._for_standards(project.atjf_standards)

    # ------------------------------------------------------------------
    # What the mail prints
    # ------------------------------------------------------------------
    def _audit_plan_dates(self):
        """(label, date) of every audit date that is filled in."""
        self.ensure_one()
        return [(label, format_date(self.env, value)) for label, value in (
            (_('Stage 1 Audit'), self.md_audit_date_st1),
            (_('Stage 2 Audit'), self.md_audit_date_st2),
            (_('Surveillance Audit'), self.md_audit_date_surveillance),
            (_('Recertification Audit'), self.md_audit_date_recert),
        ) if value]

    def _audit_plan_team(self):
        """(role, name) of the audit team."""
        self.ensure_one()
        return [(role, partner.name) for role, partner in (
            (_('Lead Auditor'), self.auditor_id),
            (_('Co-Auditor'), self.md_co_auditor_id),
            (_('Trainee'), self.md_trainee_id),
        ) if partner]

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------
    def _audit_plan_problems(self):
        self.ensure_one()
        problems = []
        if self.atjf_state != 'reviewed':
            problems.append(_('the ATJF is not reviewed yet'))
        if not self.partner_id.email:
            problems.append(_('the client %s has no e-mail address', self.partner_id.name or ''))
        if not self._audit_plan_dates():
            problems.append(_('no audit date is filled in'))
        if not self.auditor_id:
            problems.append(_('no lead auditor is assigned'))
        return problems

    def _send_audit_plan(self):
        template = self.env.ref('tuv_austria_customization.mail_template_audit_plan')
        for project in self:
            project.message_post_with_source(
                template,
                partner_ids=project.partner_id.ids,
                subtype_xmlid='mail.mt_comment',
                message_type='comment',
            )
            project.audit_plan_sent_on = fields.Datetime.now()

    def action_send_audit_plan(self):
        """The button: send it now, or say why it cannot go."""
        self.ensure_one()
        problems = self._audit_plan_problems()
        if problems:
            raise UserError(_('The audit plan cannot be sent: %s.', '; '.join(problems)))
        self._send_audit_plan()
        return True

    def action_atjf_approve(self):
        res = super().action_atjf_approve()
        # Automatic: the approved ATJF confirms the plan. A missing e-mail address must
        # not stop the review itself, so it is only noted for the planning team.
        for project in self:
            problems = project._audit_plan_problems()
            if problems:
                project.message_post(body=_(
                    'Audit plan was not sent to the client: %s.', '; '.join(problems)))
            else:
                project._send_audit_plan()
        return res
