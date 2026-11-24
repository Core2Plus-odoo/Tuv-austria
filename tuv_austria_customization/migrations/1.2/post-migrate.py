import logging

_logger = logging.getLogger(__name__)

# The document number went out as "YUV-001" by mistake; the company is TUV. The
# sequence record carries noupdate="1" so that an upgrade never resets the running
# counter, which also means the data file cannot correct the prefix on a database
# that already has it - this does. A prefix the client has since changed himself is
# left exactly as he set it.
OLD_PREFIX = 'YUV-'
NEW_PREFIX = 'TUV-'


def migrate(cr, version):
    cr.execute("""
        UPDATE ir_sequence s
           SET prefix = %s
          FROM ir_model_data d
         WHERE d.model = 'ir.sequence'
           AND d.module = 'tuv_austria_customization'
           AND d.name = 'seq_tuv_document'
           AND d.res_id = s.id
           AND s.prefix = %s
    """, (NEW_PREFIX, OLD_PREFIX))
    if cr.rowcount:
        _logger.info('Document number prefix corrected from %s to %s', OLD_PREFIX, NEW_PREFIX)
