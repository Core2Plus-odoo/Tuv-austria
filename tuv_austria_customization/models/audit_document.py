from odoo import api, fields, models


def _standard_key(name):
    """'ISO 9001:2015' / ' ISO9001' -> 'iso9001', so spellings compare equal."""
    return (name or '').split(':')[0].replace(' ', '').replace('/', '').lower()


class AuditDocument(models.Model):
    """A document the client has to have ready before the audit.

    The audit plan sent to the client lists them. A document without any standard
    is asked of every client; one with standards only of the clients audited
    against one of them.
    """

    _name = 'tuv.audit.document'
    _description = 'Audit Preparation Document'
    _order = 'sequence, id'

    name = fields.Char(string='Document', required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    certification_standard_ids = fields.Many2many(
        'certification.standard', 'tuv_audit_document_standard_rel',
        'document_id', 'standard_id', string='Only For Standards',
        help='Leave empty to ask for this document in every audit.')

    @api.model
    def _for_standards(self, standards_text):
        """The documents that belong to an audit against these standards."""
        wanted = {_standard_key(part) for part in (standards_text or '').split(',')}
        wanted.discard('')
        documents = self.search([])
        return documents.filtered(lambda doc: not doc.certification_standard_ids or any(
            _standard_key(std.name) in wanted for std in doc.certification_standard_ids))
