from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    certificate_no = fields.Char(
        related='md_sale_order_id.certificate_no', store=True, readonly=True)
    certification_standard = fields.Char(
        related='md_sale_order_id.certification_standard', store=True, readonly=True)
    ea_code_ids = fields.Many2many(
        'industry.ea.code', 'project_project_ea_code_rel', 'project_id', 'ea_code_id',
        string='EA Code', compute='_compute_ea_code_ids', store=True, readonly=False)
    scope_of_certification = fields.Char(
        related='md_sale_order_id.scope_of_certification', store=True, readonly=True)
    issue_date = fields.Date(
        related='md_sale_order_id.issue_date', store=True, readonly=True)
    expiry_date = fields.Date(
        related='md_sale_order_id.expiry_date', store=True, readonly=True)
    next_surveillance = fields.Date(
        related='md_sale_order_id.next_surveillance', store=True, readonly=True)
    audit_type = fields.Char(
        related='md_sale_order_id.audit_type', store=True, readonly=True)
    lead_auditor = fields.Selection(
        related='md_sale_order_id.lead_auditor', store=True, readonly=True)
    certificate_status = fields.Char(
        related='md_sale_order_id.certificate_status', store=True, readonly=True)
    office_issued_from = fields.Char(
        related='md_sale_order_id.office_issued_from', store=True, readonly=True)
    notes = fields.Char(
        related='md_sale_order_id.notes', store=True, readonly=True)
    contract_completed = fields.Boolean(
        related='md_sale_order_id.contract_completed', string='Contract Completed',
        store=True, readonly=True)
    contract_status = fields.Char(
        related='md_sale_order_id.contract_status', string='Contract', readonly=True)
    # Same audit team slot as on the task, so the Mandays sheet works on both.
    auditor_id = fields.Many2one(
        'res.partner', string='Auditor',
        domain="[('contact_type', '=', 'auditor'), ('approved_ea_code_ids', 'in', ea_code_ids)]")

    @api.depends('md_sale_order_id')
    def _compute_ea_code_ids(self):
        for project in self:
            project.ea_code_ids = project.md_sale_order_id.ea_code_ids


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    # Which stages count as "the audit team is currently working". It ships unticked
    # on Certificate Issuance and Feedback & Continuous Improvement (see
    # migrations/1.1), the two stages that mean the task is finished, so the team
    # parked there shows up as available again.
    auditor_busy = fields.Boolean(
        string='Occupies The Auditor', default=True,
        help='While a task sits in this stage its auditor, co-auditor and trainee are '
             'reported as Not Available in the audit team fields of other tasks.')


# The three audit-team slots. md_co_auditor_id / md_trainee_id are declared in
# project_task_mandays.py, on the same model.
AUDIT_TEAM_FIELDS = ('auditor_id', 'md_co_auditor_id', 'md_trainee_id')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    ea_code_ids = fields.Many2many(
        'industry.ea.code', 'project_task_ea_code_rel', 'task_id', 'ea_code_id',
        string='EA Code')
    # Only auditors approved for at least one of the codes picked above. With no code
    # selected the domain resolves to an empty list, so nothing is offered.
    auditor_id = fields.Many2one(
        'res.partner', string='Auditor',
        domain="[('contact_type', '=', 'auditor'), ('approved_ea_code_ids', 'in', ea_code_ids)]")

    # Core narrows the stage to the ones linked to the task's own project
    # (domain="[('project_ids', '=', project_id)]"), which is why stages that are not
    # attached to any project never appear. Stages here are shared across every project,
    # so any non-personal stage is selectable on any task - this keeps the statusbar and
    # the kanban columns showing the same set no matter how the task was opened.
    stage_id = fields.Many2one(domain="[('user_id', '=', False)]")

    def web_read(self, specification):
        """Tell the audit-team fields which task they are being displayed on.

        Those fields ask for the (Available) / (Not Available) suffix through their
        context, and the check has to skip the task at hand: a contact is not taken
        by the very task it is shown on. The view cannot supply the id on its own -
        when the client builds the read specification the record is not loaded yet,
        so evalPartialContext drops any context key that reads `id` and only the
        literal flag survives. The dropdown keeps working from the view context,
        which is evaluated later against a complete record; this fills in the gap
        for the value already stored on the task, the same way industry_fsm and
        im_livechat pass their own id down to a many2one.
        """
        if len(self) == 1:
            for field_name in AUDIT_TEAM_FIELDS:
                field_context = specification.get(field_name, {}).get('context')
                if field_context and field_context.get('show_auditor_availability'):
                    field_context['availability_exclude_task'] = self._origin.id
        return super().web_read(specification)

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        # shared (non-personal) stages always show as columns in every project's kanban
        return stages.search([('user_id', '=', False)], order=stages._order)
