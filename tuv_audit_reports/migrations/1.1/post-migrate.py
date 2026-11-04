import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Participation lists and checklists moved to the Audit Execution tab, which has its own
    # pick: a project that had one of them as its Report keeps it there (and its entries).
    env = api.Environment(cr, SUPERUSER_ID, {})
    projects = env['project.project'].with_context(active_test=False).search(
        [('audit_report_id.is_execution_form', '=', True)])
    for project in projects:
        report = project.audit_report_id
        project.write({'execution_report_id': report.id, 'execution_scheme': report.accreditation,
                       'audit_report_id': False})
    _logger.info('Execution forms moved to the Audit Execution tab on %s project(s)', len(projects))
