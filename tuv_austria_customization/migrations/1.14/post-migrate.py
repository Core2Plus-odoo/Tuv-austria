from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env['sale.order'].with_context(active_test=False).search([])
    # Contract > 1st Year Initial Audit Amount (Advance) is the proposal's Total > Initial
    # Audit now: compute it in place of the amount typed in by hand.
    env.add_to_compute(orders._fields['contract_advance_amount'], orders)
    orders._recompute_recordset(['contract_advance_amount'])
    # Contract > Standard(s) is taken from the proposal's Certification Standard: fill the
    # orders that have none yet, and keep the ones already picked on the contract.
    for order in orders.filtered(lambda o: not o.contract_standard_ids and o.certification_standard_ids):
        order.contract_standard_ids = order.certification_standard_ids
