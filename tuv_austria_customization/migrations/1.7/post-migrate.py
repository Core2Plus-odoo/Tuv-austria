import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Jobs closed before performance tracking existed get their records now.
    env = api.Environment(cr, SUPERUSER_ID, {})
    closed = env['project.project'].search([('stage_id', '!=', False)]).filtered(
        lambda p: p.stage_id._is_feedback_stage())
    closed._create_auditor_performance()
    _logger.info('Auditor performance recorded for %s closed job(s)', len(closed))
