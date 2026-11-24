from odoo import SUPERUSER_ID, api

FIELDS = ['contract_tax_y1', 'contract_tax_y2', 'contract_tax_y3',
          'contract_total_y1', 'contract_total_y2', 'contract_total_y3']


def migrate(cr, version):
    # Contract > Sales Tax and Total Payable of each year come from the proposal's Summary
    # of Cost now: compute them in place of the amounts typed in by hand.
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env['sale.order'].with_context(active_test=False).search([])
    for name in FIELDS:
        env.add_to_compute(orders._fields[name], orders)
    orders._recompute_recordset(FIELDS)
