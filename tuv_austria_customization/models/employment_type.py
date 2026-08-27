from odoo import fields, models


class EmploymentType(models.Model):
    _name = 'employment.type'
    _description = 'Employment Type'
    _order = 'name'

    name = fields.Char(required=True)
