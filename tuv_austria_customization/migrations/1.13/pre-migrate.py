import logging

_logger = logging.getLogger(__name__)

# The standard dropdowns of the order became many2many fields (several standards each):
# the old columns are kept aside here and turned into the new links by post-migrate.
OLD_COLUMNS = ('certification_standard', 'contract_standards', 'contract_service_1',
               'contract_service_2', 'contract_fee_y1', 'contract_fee_y2', 'contract_fee_y3')


def migrate(cr, version):
    for column in OLD_COLUMNS:
        cr.execute("""
            SELECT 1 FROM information_schema.columns
             WHERE table_name = 'sale_order' AND column_name = %s
        """, (column,))
        if cr.fetchone():
            cr.execute('ALTER TABLE sale_order RENAME COLUMN "%s" TO "%s_old"' % (column, column))
            _logger.info('sale_order.%s kept as %s_old', column, column)

    # The stored views of this module still name the old fields until each is reloaded,
    # and checking the first reloaded view combines it with the not yet reloaded ones:
    # rename the fields in them beforehand.
    renames = [
        (r'\mcertification_standard\M(?!_)', 'certification_standard_ids'),
        (r'\mcontract_standards\M', 'contract_standard_ids'),
        (r'\m(contract_service_[12]|contract_fee_y[123])\M(?!_)', r'\1_ids'),
    ]
    for pattern, replacement in renames:
        cr.execute("""
            UPDATE ir_ui_view v
               SET arch_db = regexp_replace(v.arch_db::text, %s, %s, 'g')::jsonb
              FROM ir_model_data d
             WHERE d.model = 'ir.ui.view' AND d.res_id = v.id
               AND d.module = 'tuv_austria_customization'
               AND v.arch_db::text ~ %s
        """, (pattern, replacement, pattern))
