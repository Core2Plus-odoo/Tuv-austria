from odoo import fields, models


class IndustryEaCode(models.Model):
    _name = 'industry.ea.code'
    _description = 'Industry / EA Code'
    _order = 'name'

    name = fields.Char(required=True)
