import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Certificates issued before the register existed are entered now, so the
    # register is complete from the first day it is used.
    env = api.Environment(cr, SUPERUSER_ID, {})
    count = env['tuv.certificate.register']._cron_register_completeness()
    _logger.info('Certificate register: %s already issued certificate(s) registered', count)
