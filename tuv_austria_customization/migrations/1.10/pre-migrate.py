import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Proposal > Invoicing Terms is the order's payment terms now (a related field, no column).
    # The old typed text is kept aside (renamed), not dropped, in case some order had one.
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'sale_order' AND column_name = 'proposal_invoicing_terms'
    """)
    if cr.fetchone():
        cr.execute("ALTER TABLE sale_order RENAME COLUMN proposal_invoicing_terms "
                   "TO proposal_invoicing_terms_old")
        cr.execute("SELECT count(*) FROM sale_order WHERE proposal_invoicing_terms_old IS NOT NULL")
        _logger.info('sale_order.proposal_invoicing_terms kept as proposal_invoicing_terms_old '
                     '(%s order(s) had a text)', cr.fetchone()[0])
