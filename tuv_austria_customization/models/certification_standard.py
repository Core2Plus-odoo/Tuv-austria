from odoo import fields, models


class CertificationStandard(models.Model):
    _name = 'certification.standard'
    _description = 'Certification Standard'
    _order = 'name'

    name = fields.Char(required=True)
