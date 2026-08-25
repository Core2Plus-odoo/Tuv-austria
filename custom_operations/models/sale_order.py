from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    certificate_no = fields.Char(string='Certificate No')
    certification_standard = fields.Char(string='Certification Standard')
    ea_code_ids = fields.Many2many('industry.ea.code', string='EA Code')
    scope_of_certification = fields.Char(string='Scope of Certification')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    next_surveillance = fields.Date(string='Next Surveillance')
    audit_type = fields.Char(string='Audit Type')
    lead_auditor = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Lead Auditor')
    certificate_status = fields.Char(string='Certificate Status')
    office_issued_from = fields.Char(string='Office Issued From')
    notes = fields.Char(string='Notes')

    def action_view_project_ids(self):
        self.ensure_one()
        projects = self.project_ids.filtered('active')
        if len(projects) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': projects.name,
                'res_model': 'project.project',
                'res_id': projects.id,
                'view_mode': 'form',
                'views': [(False, 'form')],
                'target': 'current',
            }
        return super().action_view_project_ids()

    def action_view_task_ids(self):
        self.ensure_one()
        tasks = self.tasks_ids
        action = self.env['ir.actions.actions']._for_xml_id('project.action_view_all_task')
        if len(tasks) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = tasks.id
        else:
            action['domain'] = [('id', 'in', tasks.ids)]
        return action
