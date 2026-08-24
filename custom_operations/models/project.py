from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    certificate_no = fields.Char(
        related='sale_order_id.certificate_no', store=True, readonly=True)
    certification_standard = fields.Char(
        related='sale_order_id.certification_standard', store=True, readonly=True)
    ea_code_ids = fields.Many2many(
        'industry.ea.code', 'project_project_ea_code_rel', 'project_id', 'ea_code_id',
        related='sale_order_id.ea_code_ids', string='EA Code', store=True, readonly=True)
    scope_of_certification = fields.Char(
        related='sale_order_id.scope_of_certification', store=True, readonly=True)
    issue_date = fields.Date(
        related='sale_order_id.issue_date', store=True, readonly=True)
    expiry_date = fields.Date(
        related='sale_order_id.expiry_date', store=True, readonly=True)
    next_surveillance = fields.Date(
        related='sale_order_id.next_surveillance', store=True, readonly=True)
    audit_type = fields.Char(
        related='sale_order_id.audit_type', store=True, readonly=True)
    lead_auditor = fields.Selection(
        related='sale_order_id.lead_auditor', store=True, readonly=True)
    certificate_status = fields.Char(
        related='sale_order_id.certificate_status', store=True, readonly=True)
    office_issued_from = fields.Char(
        related='sale_order_id.office_issued_from', store=True, readonly=True)
    notes = fields.Char(
        related='sale_order_id.notes', store=True, readonly=True)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        # shared (non-personal) stages always show as columns in every project's kanban
        return stages.search([('user_id', '=', False)], order=stages._order)
