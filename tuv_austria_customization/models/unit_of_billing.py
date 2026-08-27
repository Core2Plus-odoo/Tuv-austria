from odoo import fields, models


class UnitOfBilling(models.Model):
    _name = 'unit.of.billing'
    _description = 'Unit of Billing'
    _order = 'name'

    name = fields.Char(required=True)
