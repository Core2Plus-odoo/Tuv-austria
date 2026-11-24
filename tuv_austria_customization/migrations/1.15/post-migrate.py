from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # Contract > Standard(s) is read only now, always the proposal's Certification
    # Standard: compute it for every order, also those picked by hand on the contract.
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env['sale.order'].with_context(active_test=False).search([])
    env.add_to_compute(orders._fields['contract_standard_ids'], orders)
    orders._recompute_recordset(['contract_standard_ids'])
