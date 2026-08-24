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
