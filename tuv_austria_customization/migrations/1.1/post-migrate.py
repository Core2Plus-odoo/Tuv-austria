import logging

_logger = logging.getLogger(__name__)

# The two stages that mean the audit is over: everything before them keeps the
# audit team occupied, these two release it. project.task.type.auditor_busy
# defaults to True, so the stages that already existed have to be corrected once.
CLOSING_STAGES = [
    'Certificate Issuance',
    'Feedback & Continuous Improvement',
]


def migrate(cr, version):
    cr.execute("""
        UPDATE project_task_type
           SET auditor_busy = FALSE
         WHERE auditor_busy IS DISTINCT FROM FALSE
           AND name->>'en_US' IN %s
     RETURNING id
    """, (tuple(CLOSING_STAGES),))
    _logger.info(
        'Released the audit team on %s closing stage(s): %s',
        cr.rowcount, ', '.join(CLOSING_STAGES))
