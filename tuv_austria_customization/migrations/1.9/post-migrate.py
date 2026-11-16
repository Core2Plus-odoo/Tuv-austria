import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # The three Totals of Summary of Cost are sums now: replace the totals typed in before.
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env['sale.order'].with_context(active_test=False).search([])
    fields_ = [orders._fields[name] for name in ('cost_total', 'cost_tax_total', 'cost_grand_total')]
    for field in fields_:
        env.add_to_compute(field, orders)
    orders.flush_recordset()
    _logger.info('Summary of Cost totals recomputed on %s order(s)', len(orders))
