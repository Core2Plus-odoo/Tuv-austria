from odoo import models

from .audit_checklist import checklist_data

# Reference documents (the PNAC audit guidelines): printed as in Word, nothing to fill in.
# Their body is converted by tools/docx_forms.py into data/checklists/<key>.json.
DOCUMENT_PREFIX = 'doc_'


class AuditInfoMixin(models.AbstractModel):
    _inherit = 'tuv.audit.info.mixin'

    def _doc_payload(self):
        """The converted Word document selected on this record (audit_report_key doc_<key>)."""
        self.ensure_one()
        return checklist_data((self.audit_report_key or '').removeprefix(DOCUMENT_PREFIX))
