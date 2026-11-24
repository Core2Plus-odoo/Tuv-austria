import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # The STI sequence went out as a "standard" (PostgreSQL) sequence, which skips a
    # number whenever a transaction is rolled back. Sales tax invoice serials must not
    # have gaps; the record is noupdate, so the data file cannot switch it.
    env = api.Environment(cr, SUPERUSER_ID, {})
    seq = env.ref('tuv_austria_customization.seq_tuv_sales_tax_invoice', raise_if_not_found=False)
    if not seq or seq.implementation == 'no_gap':
        return
    # the running counter lives in the PostgreSQL sequence while "standard": carry it
    # over, or the no-gap counter would restart at 1 and hand out numbers again
    next_number = seq.number_next_actual
    seq.write({'implementation': 'no_gap', 'number_next': next_number})
    _logger.info('Sales Tax Invoice sequence switched to no-gap numbering, next number %s', next_number)
