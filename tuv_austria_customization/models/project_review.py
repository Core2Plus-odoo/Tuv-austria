from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    """The planning team's side of an order.

    The project is created the moment sales sends the review form over, and shows
    the very same review form and contract, read only: the planning team checks
    what sales filled in and either approves it or sends it back. Everything is a
    related field on the order (md_sale_order_id), so there is one copy of the data.
    """

    _inherit = 'project.project'

    review_state = fields.Selection(
        related='md_sale_order_id.review_state', string='Review Status', readonly=True)
    # What the planning team sees on their own statusbar: the review is either still
    # theirs to do (Draft) or done (Approved).
    review_approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ], string='Review', compute='_compute_review_approval_state')

    @api.depends('review_state')
    def _compute_review_approval_state(self):
        for project in self:
            project.review_approval_state = (
                'approved' if project.review_state == 'review_approved' else 'draft')
    review_submitted_by = fields.Many2one(
        related='md_sale_order_id.review_submitted_by', readonly=True)
    review_submitted_on = fields.Datetime(
        related='md_sale_order_id.review_submitted_on', readonly=True)
    review_approved_by = fields.Many2one(
        related='md_sale_order_id.review_approved_by', readonly=True)
    review_approved_on = fields.Datetime(
        related='md_sale_order_id.review_approved_on', readonly=True)
    document_type = fields.Selection(
        related='md_sale_order_id.document_type', string='Document Type', readonly=True)
    document_stage = fields.Integer(related='md_sale_order_id.document_stage', readonly=True)

    # ------------------------------------------------------------------
    # Review form and contract of the order, read only
    # ------------------------------------------------------------------
    rf_audit_type = fields.Selection(related='md_sale_order_id.rf_audit_type', readonly=True)
    rf_certified_since = fields.Date(related='md_sale_order_id.rf_certified_since', readonly=True)
    rf_competent = fields.Selection(related='md_sale_order_id.rf_competent', readonly=True)
    rf_date = fields.Date(related='md_sale_order_id.rf_date', readonly=True)
    rf_docs_reviewed = fields.Boolean(related='md_sale_order_id.rf_docs_reviewed', readonly=True)
    rf_iaf_code = fields.Char(related='md_sale_order_id.rf_iaf_code', readonly=True)
    rf_ic_dates = fields.Char(related='md_sale_order_id.rf_ic_dates', readonly=True)
    rf_ic_nc = fields.Char(related='md_sale_order_id.rf_ic_nc', readonly=True)
    rf_ic_nc_status = fields.Char(related='md_sale_order_id.rf_ic_nc_status', readonly=True)
    rf_ic_report_reviewed = fields.Char(related='md_sale_order_id.rf_ic_report_reviewed', readonly=True)
    rf_impartiality_risk = fields.Selection(related='md_sale_order_id.rf_impartiality_risk', readonly=True)
    rf_info_sufficient = fields.Selection(related='md_sale_order_id.rf_info_sufficient', readonly=True)
    rf_iso_14001 = fields.Boolean(related='md_sale_order_id.rf_iso_14001', readonly=True)
    rf_iso_22000 = fields.Boolean(related='md_sale_order_id.rf_iso_22000', readonly=True)
    rf_iso_45001 = fields.Boolean(related='md_sale_order_id.rf_iso_45001', readonly=True)
    rf_iso_9001 = fields.Boolean(related='md_sale_order_id.rf_iso_9001', readonly=True)
    rf_others = fields.Boolean(related='md_sale_order_id.rf_others', readonly=True)
    rf_others_text = fields.Char(related='md_sale_order_id.rf_others_text', readonly=True)
    rf_outcome = fields.Selection(related='md_sale_order_id.rf_outcome', readonly=True)
    rf_reports_evaluated = fields.Boolean(related='md_sale_order_id.rf_reports_evaluated', readonly=True)
    rf_reviewer_name = fields.Char(related='md_sale_order_id.rf_reviewer_name', readonly=True)
    rf_s1_dates = fields.Char(related='md_sale_order_id.rf_s1_dates', readonly=True)
    rf_s1_nc = fields.Char(related='md_sale_order_id.rf_s1_nc', readonly=True)
    rf_s1_nc_status = fields.Char(related='md_sale_order_id.rf_s1_nc_status', readonly=True)
    rf_s1_report_reviewed = fields.Char(related='md_sale_order_id.rf_s1_report_reviewed', readonly=True)
    rf_s2_dates = fields.Char(related='md_sale_order_id.rf_s2_dates', readonly=True)
    rf_s2_nc = fields.Char(related='md_sale_order_id.rf_s2_nc', readonly=True)
    rf_s2_nc_status = fields.Char(related='md_sale_order_id.rf_s2_nc_status', readonly=True)
    rf_s2_report_reviewed = fields.Char(related='md_sale_order_id.rf_s2_report_reviewed', readonly=True)
    rf_scope = fields.Text(related='md_sale_order_id.rf_scope', readonly=True)
    rf_signature = fields.Binary(related='md_sale_order_id.rf_signature', readonly=True)
    rf_signature_filename = fields.Char(related='md_sale_order_id.rf_signature_filename', readonly=True)
    rf_specify = fields.Char(related='md_sale_order_id.rf_specify', readonly=True)
    rf_standards = fields.Char(related='md_sale_order_id.rf_standards', readonly=True)
    contract_accreditation_1 = fields.Char(related='md_sale_order_id.contract_accreditation_1', readonly=True)
    contract_accreditation_2 = fields.Char(related='md_sale_order_id.contract_accreditation_2', readonly=True)
    contract_address_1 = fields.Char(related='md_sale_order_id.contract_address_1', readonly=True)
    contract_address_2 = fields.Char(related='md_sale_order_id.contract_address_2', readonly=True)
    contract_advance_amount = fields.Char(related='md_sale_order_id.contract_advance_amount', readonly=True)
    contract_date = fields.Date(related='md_sale_order_id.contract_date', readonly=True)
    contract_designation = fields.Char(related='md_sale_order_id.contract_designation', readonly=True)
    contract_fee_y1 = fields.Char(related='md_sale_order_id.contract_fee_y1', readonly=True)
    contract_fee_y2 = fields.Char(related='md_sale_order_id.contract_fee_y2', readonly=True)
    contract_fee_y3 = fields.Char(related='md_sale_order_id.contract_fee_y3', readonly=True)
    contract_mandays_y1 = fields.Char(related='md_sale_order_id.contract_mandays_y1', readonly=True)
    contract_mandays_y2 = fields.Char(related='md_sale_order_id.contract_mandays_y2', readonly=True)
    contract_mandays_y3 = fields.Char(related='md_sale_order_id.contract_mandays_y3', readonly=True)
    contract_ref = fields.Char(related='md_sale_order_id.contract_ref', readonly=True)
    contract_representative = fields.Char(related='md_sale_order_id.contract_representative', readonly=True)
    contract_service_1 = fields.Char(related='md_sale_order_id.contract_service_1', readonly=True)
    contract_service_2 = fields.Char(related='md_sale_order_id.contract_service_2', readonly=True)
    contract_standards = fields.Char(related='md_sale_order_id.contract_standards', readonly=True)
    contract_tax_province = fields.Char(related='md_sale_order_id.contract_tax_province', readonly=True)
    contract_tax_y1 = fields.Char(related='md_sale_order_id.contract_tax_y1', readonly=True)
    contract_tax_y2 = fields.Char(related='md_sale_order_id.contract_tax_y2', readonly=True)
    contract_tax_y3 = fields.Char(related='md_sale_order_id.contract_tax_y3', readonly=True)
    contract_total_y1 = fields.Char(related='md_sale_order_id.contract_total_y1', readonly=True)
    contract_total_y2 = fields.Char(related='md_sale_order_id.contract_total_y2', readonly=True)
    contract_total_y3 = fields.Char(related='md_sale_order_id.contract_total_y3', readonly=True)

    # ------------------------------------------------------------------
    # The planning team acts from here
    # ------------------------------------------------------------------
    def _review_order(self):
        self.ensure_one()
        order = self.md_sale_order_id
        if not order:
            raise UserError(_('This project is not linked to a sales order.'))
        return order

    # ------------------------------------------------------------------
    # Moving through the stages, one button at a time
    # ------------------------------------------------------------------
    stage_name = fields.Char(related='stage_id.name', string='Stage Name', readonly=True)

    def action_move_next_stage(self):
        """Send the project to the next stage of the flow.

        Every header button calls this one method; which button is on screen is
        decided by the stage the project is in, so only the step ahead is offered.
        """
        self.ensure_one()
        following = self.env['project.project.stage'].sudo().search(
            [('sequence', '>=', self.stage_id.sequence), ('id', '!=', self.stage_id.id)],
            order='sequence, id', limit=1)
        if not following:
            raise UserError(_('%s is already in the last stage.', self.name))
        self.stage_id = following.id
        return True

    def action_approve_review(self):
        return self._review_order().action_approve_review()

    def action_reject_review(self):
        return self._review_order().action_reject_review()
