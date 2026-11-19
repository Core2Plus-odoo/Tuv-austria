from odoo import SUPERUSER_ID, api

from odoo.addons.tuv_austria_customization.models.project_task_mandays import MD_STANDARD

# old dropdown column -> new many2many field
FIELDS = {
    'certification_standard_old': 'certification_standard_ids',
    'contract_standards_old': 'contract_standard_ids',
    'contract_service_1_old': 'contract_service_1_ids',
    'contract_service_2_old': 'contract_service_2_ids',
    'contract_fee_y1_old': 'contract_fee_y1_ids',
    'contract_fee_y2_old': 'contract_fee_y2_ids',
    'contract_fee_y3_old': 'contract_fee_y3_ids',
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Standard = env['certification.standard']
    labels = dict(MD_STANDARD)
    for column, field in FIELDS.items():
        cr.execute("""
            SELECT 1 FROM information_schema.columns
             WHERE table_name = 'sale_order' AND column_name = %s
        """, (column,))
        if not cr.fetchone():
            continue
        cr.execute('SELECT id, "%s" FROM sale_order WHERE "%s" IS NOT NULL' % (column, column))
        for order_id, code in cr.fetchall():
            standards = Standard._from_names([labels.get(code, code)])
            if standards:
                env['sale.order'].browse(order_id).write({field: [(6, 0, standards.ids)]})
