from odoo import _, api, fields, models
from odoo.exceptions import UserError

RF_YESNO = [('yes', 'Yes'), ('no', 'No')]
RF_AUDIT_TYPE = [
    ('initial_certification', 'Initial Certification'),
    ('recertification', 'Recertification'),
]
RF_OUTCOME = [
    ('accepted', 'Application Accepted'),
    ('not_accepted', 'Application Not Accepted'),
]

# Every field of "8. Application Review Form.docx" (TUV/BA/FM/02-2, Rev 00), in the
# order of the printed form. The planning team reads these; only sales fills them.
REVIEW_FIELDS = (
    'rf_competent', 'rf_info_sufficient', 'rf_impartiality_risk', 'rf_specify',
    'rf_audit_type', 'rf_scope', 'rf_iaf_code', 'rf_standards',
    'rf_certified_since', 'rf_iso_9001', 'rf_iso_14001', 'rf_iso_45001', 'rf_iso_22000',
    'rf_others', 'rf_others_text', 'rf_docs_reviewed', 'rf_reports_evaluated',
    'rf_ic_dates', 'rf_ic_report_reviewed', 'rf_ic_nc', 'rf_ic_nc_status',
    'rf_s1_dates', 'rf_s1_report_reviewed', 'rf_s1_nc', 'rf_s1_nc_status',
    'rf_s2_dates', 'rf_s2_report_reviewed', 'rf_s2_nc', 'rf_s2_nc_status',
    'rf_outcome', 'rf_reviewer_name', 'rf_signature', 'rf_date',
)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ------------------------------------------------------------------
    # Review workflow
    # ------------------------------------------------------------------
    review_state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_review', 'Waiting for Review'),
        ('review_approved', 'Review Approved'),
    ], string='Review Status', default='draft', copy=False, tracking=True, required=True,
        help='Draft while sales fills the review form, Waiting for Review once it is sent '
             'to the planning team, Review Approved after they accept it.')
    review_submitted_on = fields.Datetime(string='Sent for Review On', readonly=True, copy=False)
    review_submitted_by = fields.Many2one('res.users', string='Sent for Review By', readonly=True, copy=False)
    review_approved_on = fields.Datetime(string='Review Approved On', readonly=True, copy=False)
    review_approved_by = fields.Many2one('res.users', string='Review Approved By', readonly=True, copy=False)
    # Sales cannot touch the order while the planning team has it.
    review_locked = fields.Boolean(compute='_compute_review_locked')

    # One single bar for the whole flow: the review status and the document type
    # folded into the one line the user follows from draft to contract.
    flow_state = fields.Selection([
        ('draft', 'Draft'),
        ('review_form', 'Review Form'),
        ('waiting_review', 'Waiting for Review'),
        ('review_approved', 'Review Approved'),
        ('offer_application', 'Offer Application'),
        ('proposal_form', 'Proposal Form'),
        ('contract', 'Contract'),
    ], string='Flow', compute='_compute_flow_state', store=True, index=True)

    @api.depends('review_state', 'document_type')
    def _compute_flow_state(self):
        for order in self:
            if order.review_state == 'waiting_review':
                order.flow_state = 'waiting_review'
            elif order.review_state == 'draft':
                order.flow_state = 'review_form' if order.document_type == 'review_form' else 'draft'
            elif order.document_type in ('contract_form', 'pnac_contract'):
                order.flow_state = 'contract'
            elif order.document_type in ('offer_application', 'proposal_form'):
                order.flow_state = order.document_type
            else:
                order.flow_state = 'review_approved'

    @api.depends('review_state')
    def _compute_review_locked(self):
        for order in self:
            order.review_locked = order.review_state == 'waiting_review'

    # ------------------------------------------------------------------
    # COMPETENCE EVALUATION & IMPARTIALITY CHECK
    # ------------------------------------------------------------------
    rf_competent = fields.Selection(
        RF_YESNO, string='Is TUV competent to perform certification activity?')
    rf_info_sufficient = fields.Selection(
        RF_YESNO, string='Is the information provided by client sufficient to develop Audit Program?')
    rf_impartiality_risk = fields.Selection(
        RF_YESNO, string='Is there any information which can influence certification activity '
                         'like threats to impartiality, safety conditions, sites, operations etc.?')
    rf_specify = fields.Char(string='If yes, please specify')

    # AUDIT TYPE
    rf_audit_type = fields.Selection(RF_AUDIT_TYPE, string='Review Audit Type')

    # CLIENT INFORMATION (client name is the order's customer)
    rf_scope = fields.Text(string='Review Scope')
    rf_iaf_code = fields.Char(string='Applicable IAF Code')
    rf_standards = fields.Char(string='Standards')

    # CERTIFICATION HISTORY (for recertification only)
    rf_certified_since = fields.Date(string='This Client Is Certified Since')
    rf_iso_9001 = fields.Boolean(string='ISO 9001:2015')
    rf_iso_14001 = fields.Boolean(string='ISO 14001:2015')
    rf_iso_45001 = fields.Boolean(string='ISO 45001:2018')
    rf_iso_22000 = fields.Boolean(string='ISO 22000:2018')
    rf_others = fields.Boolean(string='Others')
    rf_others_text = fields.Char(string='Others (specify)')
    rf_docs_reviewed = fields.Boolean(
        string='All audit documentation from the previous cycle has been reviewed')
    rf_reports_evaluated = fields.Boolean(
        string='Reports were evaluated and the following activities were verified as closed')

    # RECERTIFICATION AUDIT SUMMARY (if applicable)
    rf_ic_dates = fields.Char(string='Initial Certification - Audit Dates')
    rf_ic_report_reviewed = fields.Char(string='Initial Certification - Report Reviewed (Yes/No)')
    rf_ic_nc = fields.Char(string='Initial Certification - Non-Conformities')
    rf_ic_nc_status = fields.Char(string='Initial Certification - Status Of Nonconformities')
    rf_s1_dates = fields.Char(string='Surveillance 01 - Audit Dates')
    rf_s1_report_reviewed = fields.Char(string='Surveillance 01 - Report Reviewed (Yes/No)')
    rf_s1_nc = fields.Char(string='Surveillance 01 - Non-Conformities')
    rf_s1_nc_status = fields.Char(string='Surveillance 01 - Status Of Nonconformities')
    rf_s2_dates = fields.Char(string='Surveillance 02 - Audit Dates')
    rf_s2_report_reviewed = fields.Char(string='Surveillance 02 - Report Reviewed (Yes/No)')
    rf_s2_nc = fields.Char(string='Surveillance 02 - Non-Conformities')
    rf_s2_nc_status = fields.Char(string='Surveillance 02 - Status Of Nonconformities')

    # REVIEW OUTCOME
    rf_outcome = fields.Selection(RF_OUTCOME, string='Review Outcome')
    rf_reviewer_name = fields.Char(string='Reviewer Name')
    rf_signature = fields.Binary(string='Reviewer Signature', attachment=True)
    rf_signature_filename = fields.Char(string='Reviewer Signature Filename')
    rf_date = fields.Date(string='Review Date')

    # ------------------------------------------------------------------
    # Sales -> Planning
    # ------------------------------------------------------------------
    def _review_planning_users(self):
        """Everybody who has to look at a review form."""
        group = self.env.ref('tuv_austria_customization.group_planning_team',
                             raise_if_not_found=False)
        if not group:
            return self.env['res.users']
        # all_group_ids covers users who get the group through an implied one
        return self.env['res.users'].search([('all_group_ids', 'in', group.id)])

    def _review_notified_users(self):
        """Planning team + the administrator, who must see everything."""
        users = self._review_planning_users()
        admin = self.env.ref('base.user_admin', raise_if_not_found=False)
        if admin and admin.active:
            users |= admin
        return users

    def action_submit_to_planning(self):
        self.ensure_one()
        if self.review_state != 'draft':
            raise UserError(_('This order has already been sent to the planning team.'))
        if not self.rf_outcome:
            raise UserError(_('Fill in the Review Outcome before sending the review form '
                              'to the planning team.'))
        self.write({
            'document_type': 'review_form',
            'review_state': 'waiting_review',
            'review_submitted_on': fields.Datetime.now(),
            'review_submitted_by': self.env.user.id,
        })
        # The project starts here, not at the contract: the planning team needs
        # somewhere to do the review.
        # sudo: project_ids is readable only by project users, and a salesperson is
        # usually not one.
        project = self.sudo().project_ids[:1] or self._create_order_project()
        self.invalidate_recordset(['project_ids', 'project_count'])

        users = self._review_notified_users()
        body = _('Review form of %(order)s was sent to the planning team by %(user)s.',
                 order=self.name, user=self.env.user.name)
        # message_post with recipients = chatter entry + outgoing e-mail
        self.message_post(body=body, partner_ids=users.partner_id.ids,
                          subtype_xmlid='mail.mt_comment')
        summary = _('Review form to check - %s', self.name)
        note = _('Sales sent the application review form of %s for approval.', self.name)
        for user in self._review_planning_users():
            self.activity_schedule('mail.mail_activity_data_todo', user_id=user.id,
                                   summary=summary, note=note)
            if project:
                project.sudo().activity_schedule('mail.mail_activity_data_todo', user_id=user.id,
                                                 summary=summary, note=note)
        if project:
            project.sudo().message_post(body=body, partner_ids=users.partner_id.ids,
                                        subtype_xmlid='mail.mt_comment')
        return True

    # ------------------------------------------------------------------
    # Planning -> Sales
    # ------------------------------------------------------------------
    def action_approve_review(self):
        self.ensure_one()
        if self.review_state != 'waiting_review':
            raise UserError(_('Only an order waiting for review can be approved.'))
        # sudo: a planning user has no write access on sale.order, the group is what
        # authorises them here.
        self.sudo().write({
            'review_state': 'review_approved',
            'review_approved_on': fields.Datetime.now(),
            'review_approved_by': self.env.user.id,
        })
        # the project moves on to Review Approved
        stage = self.env.ref('tuv_austria_customization.project_stage_review_approved',
                             raise_if_not_found=False)
        if stage:
            self.sudo().project_ids.sudo().write({'stage_id': stage.id})
        # the planning team is done with it
        self.sudo().activity_feedback(['mail.mail_activity_data_todo'])
        for project in self.sudo().project_ids:
            project.sudo().activity_feedback(['mail.mail_activity_data_todo'])

        body = _('Review form of %(order)s was approved by %(user)s. Sales can continue with '
                 'the application form, the proposal and the contract.',
                 order=self.name, user=self.env.user.name)
        salespeople = self.sudo().user_id | self.sudo().create_uid
        self.sudo().message_post(body=body, partner_ids=salespeople.partner_id.ids,
                                 subtype_xmlid='mail.mt_comment')
        for user in salespeople:
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo', user_id=user.id,
                summary=_('Review approved - %s', self.name),
                note=_('The planning team approved the review form. Continue with the '
                       'application form, the proposal and the contract.'))
        return True

    def action_reject_review(self):
        """Send it back to sales so the form can be corrected."""
        self.ensure_one()
        if self.review_state != 'waiting_review':
            raise UserError(_('Only an order waiting for review can be sent back.'))
        self.sudo().write({'review_state': 'draft'})
        self.sudo().activity_feedback(['mail.mail_activity_data_todo'])
        for project in self.sudo().project_ids:
            project.sudo().activity_feedback(['mail.mail_activity_data_todo'])
        salespeople = self.user_id | self.create_uid
        body = _('Review form of %(order)s was sent back to sales by %(user)s.',
                 order=self.name, user=self.env.user.name)
        self.message_post(body=body, partner_ids=salespeople.partner_id.ids,
                          subtype_xmlid='mail.mt_comment')
        for user in salespeople:
            self.activity_schedule(
                'mail.mail_activity_data_todo', user_id=user.id,
                summary=_('Review form sent back - %s', self.name),
                note=_('The planning team asked for corrections on the review form.'))
        return True

    # ------------------------------------------------------------------
    # Contract hand over
    # ------------------------------------------------------------------
    def action_send_contract_to_planning(self):
        """Hand the finished contract to the planning team."""
        self.ensure_one()
        if self.document_type not in ('contract_form', 'pnac_contract'):
            raise UserError(_('Pick a contract document type first.'))
        users = self._review_notified_users()
        body = _('Contract of %(order)s was sent to the planning team by %(user)s.',
                 order=self.name, user=self.env.user.name)
        self.message_post(body=body, partner_ids=users.partner_id.ids,
                          subtype_xmlid='mail.mt_comment')
        summary = _('Contract received - %s', self.name)
        note = _('Sales finished the contract of %s. The details are on the Contract tab '
                 'of this project.', self.name)
        for project in self.sudo().project_ids:
            project.sudo().message_post(body=body, partner_ids=users.partner_id.ids,
                                        subtype_xmlid='mail.mt_comment')
            for user in self._review_planning_users():
                project.sudo().activity_schedule('mail.mail_activity_data_todo',
                                                 user_id=user.id, summary=summary, note=note)
        return True

    # ------------------------------------------------------------------
    # While the planning team has it, sales is locked out
    # ------------------------------------------------------------------
    # Only the review workflow itself and the chatter may still move.
    _REVIEW_UNLOCKED_FIELDS = frozenset({
        'review_state', 'review_approved_on', 'review_approved_by',
        'review_submitted_on', 'review_submitted_by',
        'message_follower_ids', 'message_ids', 'activity_ids', 'message_main_attachment_id',
        'access_token',
    })

    def write(self, vals):
        touched = set(vals) - self._REVIEW_UNLOCKED_FIELDS
        if touched and not self.env.su:
            planning = self.env.user.has_group('tuv_austria_customization.group_planning_team')
            if not planning:
                blocked = self.filtered(lambda o: o.review_state == 'waiting_review')
                if blocked:
                    raise UserError(_(
                        'The review form of %s is with the planning team. Wait for their '
                        'approval before changing the order.',
                        ', '.join(blocked.mapped('name'))))
        return super().write(vals)
