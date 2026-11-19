from odoo import api, fields, models

from .audit_document import _standard_key


class CertificationStandard(models.Model):
    _name = 'certification.standard'
    _description = 'Certification Standard'
    _order = 'name'

    name = fields.Char(required=True)

    @api.model
    def _from_names(self, names):
        """The standards matching these names ('ISO9001:2015' finds 'ISO 9001'),
        created when the list has none of that name yet."""
        existing = {}
        for standard in self.search([]):
            existing.setdefault(_standard_key(standard.name), standard)
        result = self.browse()
        for name in names:
            key = _standard_key(name)
            if not key:
                continue
            if key not in existing:
                existing[key] = self.create({'name': name.strip()})
            result |= existing[key]
        return result
