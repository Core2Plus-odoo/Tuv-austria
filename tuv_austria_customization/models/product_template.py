from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    service_category_ids = fields.Many2many('service.category', string='Service Category')
    certification_standard_ids = fields.Many2many(
        'certification.standard', string='Certification Standard')
    code_applicable_ids = fields.Many2many(
        'industry.ea.code', 'product_template_code_applicable_rel',
        'product_tmpl_id', 'ea_code_id', string='Code Applicable')
    unit_of_billing_id = fields.Many2one('unit.of.billing', string='Unit of Billing')

    # hardcoded to PKR/USD regardless of company currency, so the two rates never share a currency
    man_day_rate_pkr_currency_id = fields.Many2one(
        'res.currency', compute='_compute_man_day_rate_currencies', store=True)
    man_day_rate_usd_currency_id = fields.Many2one(
        'res.currency', compute='_compute_man_day_rate_currencies', store=True)
    man_day_rate_pkr = fields.Monetary(
        string='Man-Day Rate (PKR)', currency_field='man_day_rate_pkr_currency_id')
    man_day_rate_usd = fields.Monetary(
        string='Man-Day Rate (USD)', currency_field='man_day_rate_usd_currency_id')

    min_man_days = fields.Char(string='Min Man-Days')
    max_man_days = fields.Char(string='Max Man-Days')

    tax_applicable = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Tax Applicable')

    @api.depends()
    def _compute_man_day_rate_currencies(self):
        currency_model = self.env['res.currency'].with_context(active_test=False)
        pkr = currency_model.search([('name', '=', 'PKR')], limit=1)
        usd = currency_model.search([('name', '=', 'USD')], limit=1)
        for product in self:
            product.man_day_rate_pkr_currency_id = pkr
            product.man_day_rate_usd_currency_id = usd
