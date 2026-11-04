import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Certificate texts moved to the Certificate Dispatched tab, which has its own pick: a
    # project that had one of them as its Report keeps it there (and its entries).
    env = api.Environment(cr, SUPERUSER_ID, {})
    projects = env['project.project'].with_context(active_test=False).search(
        [('audit_report_id.is_certificate_form', '=', True)])
    for project in projects:
        report = project.audit_report_id
        project.write({'dispatch_report_id': report.id, 'dispatch_scheme': report.accreditation,
                       'audit_report_id': False})
    _logger.info('Certificate texts moved to the Certificate Dispatched tab on %s project(s)', len(projects))
