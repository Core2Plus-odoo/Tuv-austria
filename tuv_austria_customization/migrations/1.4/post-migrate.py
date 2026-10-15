import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Audits completed before the nonconformity register existed never logged their
    # NCs; log them now, with deadlines counted from their own completion date.
    env = api.Environment(cr, SUPERUSER_ID, {})
    projects = env['project.project'].with_context(active_test=False).search(
        [('audit_state', '=', 'done')])
    projects._sync_nonconformities()
    _logger.info('Nonconformities logged for %s completed audit(s): %s NC(s)',
                 len(projects), len(projects.nonconformity_ids))
