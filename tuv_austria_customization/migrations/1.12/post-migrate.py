from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # Proposal > Summary of Cost > Total is now fee + sales tax of each audit: compute it
    # for the existing orders instead of keeping the numbers typed in by hand.
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env['sale.order'].with_context(active_test=False).search([])
    fields_ = ['cost_grand_initial_audit', 'cost_grand_surveillance_1',
               'cost_grand_surveillance_2', 'cost_grand_total']
    for name in fields_:
        env.add_to_compute(orders._fields[name], orders)
    orders._recompute_recordset(fields_)
