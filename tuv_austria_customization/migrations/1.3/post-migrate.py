import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # project.audit_document_ids is computed when the column is created, which is
    # before data/audit_document_data.xml has loaded the documents - so every
    # project that already existed got an empty list. Fill it in once.
    env = api.Environment(cr, SUPERUSER_ID, {})
    projects = env['project.project'].with_context(active_test=False).search(
        [('audit_document_ids', '=', False)])
    Document = env['tuv.audit.document']
    for project in projects:
        project.audit_document_ids = Document._for_standards(project.atjf_standards)
    _logger.info('Audit documents filled in on %s existing project(s)', len(projects))
