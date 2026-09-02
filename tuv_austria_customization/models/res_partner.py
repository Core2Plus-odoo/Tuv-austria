from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    telefax = fields.Char(string='Telefax')
    distinctive_title = fields.Char(string='Distinctive Title')
    contact_type = fields.Selection([
        ('client', 'Client'),
        ('vendor', 'Vendor'),
        ('auditor', 'Auditor'),
    ], string='Contact Type')
    industry_ea_code_id = fields.Many2one('industry.ea.code', string='Industry/EA Code')
    cnic = fields.Char(string='CNIC')

    employment_type_ids = fields.Many2many('employment.type', string='Employment Type')
    approved_ea_code_ids = fields.Many2many(
        'industry.ea.code', 'res_partner_approved_ea_code_rel',
        'partner_id', 'ea_code_id', string='Approved EA Codes')
    certification_standard_ids = fields.Many2many(
        'certification.standard', string='Certification Standards Competent In')
    auditor_category_ids = fields.Many2many('auditor.category', string='Auditor Category')
    lead_auditor = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Lead Auditor?')
    # named auditor_active, not active: 'active' is reserved by Odoo for record archiving
    auditor_active = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Active?')
    auditor_notes = fields.Char(string='Notes/Restrictions')
