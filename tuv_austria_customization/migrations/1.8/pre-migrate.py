import logging
import re

_logger = logging.getLogger(__name__)

# The 8 "Standard" fields of the sale order became dropdowns of the Mandays standards
# (MD_STANDARD of models/project_task_mandays.py). Before the new fields load, the text typed
# in them is turned into the matching dropdown value; what matches nothing is emptied.
# contract_fee_y1/2/3 held the fee amounts: emptied, as the user asked (16.11.2026).
STANDARD_FIELDS = ('certification_standard', 'contract_standards', 'contract_service_1',
                   'contract_service_2', 'rf_standards')
FEE_FIELDS = ('contract_fee_y1', 'contract_fee_y2', 'contract_fee_y3')

# a copy of MD_STANDARD: a migration must not import the module's models
MD_STANDARD = [
    ('iso9001_2015', 'ISO9001:2015'), ('iso14001_2015', 'ISO14001:2015'),
    ('iso22000_2018', 'ISO22000:2018'), ('iso22000_2005', 'ISO22000:2005'),
    ('fssc22000', 'FSSC22000'), ('ohsas18001', 'OHSAS18001'), ('iso45001', 'ISO45001'),
    ('iso27001', 'ISO27001'), ('iso22301', 'ISO22301'), ('iso50001', 'ISO50001'),
    ('iso39001', 'ISO39001'), ('iso13485', 'ISO13485'), ('emas_iii', 'EMAS III'),
    ('iso_iec20000', 'ISO/IEC20000'), ('globalgap', 'GLOBALGAP'), ('iso37001', 'ISO37001'),
    ('en15224_2016', 'EN15224:2016'), ('iso22716', 'ISO22716'),
]


def _key(text):
    """'ISO: 9001' / 'ISO 9001:2015' -> 'iso9001'; 'EMAS III' -> 'emasiii'."""
    text = (text or '').split(',')[0].split(':2')[0]
    return re.sub(r'[^a-z0-9]', '', text.lower())


def migrate(cr, version):
    codes = {}
    for code, label in MD_STANDARD:     # ISO22000:2018 before ISO22000:2005
        codes.setdefault(_key(label), code)
        codes.setdefault(code, code)    # already a dropdown value
    for column in STANDARD_FIELDS:
        cr.execute("SELECT id, %s FROM sale_order WHERE %s IS NOT NULL" % (column, column))
        for order_id, text in cr.fetchall():
            code = codes.get(_key(text)) or codes.get(text)
            if code != text:
                cr.execute("UPDATE sale_order SET %s = %%s WHERE id = %%s" % column, (code, order_id))
                _logger.info('sale.order %s %s: %r -> %r', order_id, column, text, code)
    for column in FEE_FIELDS:
        cr.execute("UPDATE sale_order SET %s = NULL WHERE %s IS NOT NULL" % (column, column))
        _logger.info('sale.order %s emptied on %s order(s)', column, cr.rowcount)
    # the project keeps a stored copy of the order's certification standard
    cr.execute("""
        UPDATE project_project p SET certification_standard = so.certification_standard
          FROM sale_order so
         WHERE p.md_sale_order_id = so.id
           AND p.certification_standard IS DISTINCT FROM so.certification_standard
    """)
    _logger.info('project.project certification_standard synced on %s project(s)', cr.rowcount)
