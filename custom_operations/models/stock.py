from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # TODO: add inventory/delivery customization fields here
