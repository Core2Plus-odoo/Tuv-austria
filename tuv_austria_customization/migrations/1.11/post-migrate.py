from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # The review form now comes before the planning team's review, so the stored flow
    # bar of the existing orders is computed again with the new order of the stages.
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env['sale.order'].with_context(active_test=False).search([])
    env.add_to_compute(orders._fields['flow_state'], orders)
    orders._recompute_recordset(['flow_state'])
