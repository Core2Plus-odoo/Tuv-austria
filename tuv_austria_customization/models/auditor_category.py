from odoo import fields, models


class AuditorCategory(models.Model):
    _name = 'auditor.category'
    _description = 'Auditor Category'
    _order = 'name'

    name = fields.Char(required=True)
