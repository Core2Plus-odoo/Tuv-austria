import logging

_logger = logging.getLogger(__name__)

# Proposal > Summary of Cost: the 12 amounts were typed in as text and are numbers now.
# The text becomes a number in place ("1500", "$1,500.00", "USD 1500" -> 1500.0; anything
# without a number -> empty) before the fields load, so Odoo does not set the old column aside.
COLUMNS = (
    'cost_initial_audit', 'cost_surveillance_1', 'cost_surveillance_2', 'cost_total',
    'cost_tax_initial_audit', 'cost_tax_surveillance_1', 'cost_tax_surveillance_2', 'cost_tax_total',
    'cost_grand_initial_audit', 'cost_grand_surveillance_1', 'cost_grand_surveillance_2', 'cost_grand_total',
)


def migrate(cr, version):
    for column in COLUMNS:
        cr.execute("""
            SELECT data_type FROM information_schema.columns
             WHERE table_name = 'sale_order' AND column_name = %s
        """, (column,))
        row = cr.fetchone()
        if not row or row[0] not in ('character varying', 'text'):
            continue
        # keep digits and the decimal point; '' or a lone '.' is no number
        cr.execute("""
            ALTER TABLE sale_order ALTER COLUMN %(col)s TYPE double precision
            USING NULLIF(NULLIF(regexp_replace(%(col)s, '[^0-9.]', '', 'g'), ''), '.')::double precision
        """ % {'col': column})
        _logger.info('sale_order.%s converted to a number', column)
