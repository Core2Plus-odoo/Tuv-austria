from odoo import fields, models


class ServiceCategory(models.Model):
    _name = 'service.category'
    _description = 'Service Category'
    _order = 'name'

    name = fields.Char(required=True)
