def migrate(cr, version):
    # The view that only hid the Audit Evidence tab is replaced by the Certificate Dispatched
    # tab (which takes that page's place): drop it first, or the new view finds no page to replace.
    cr.execute("""
        DELETE FROM ir_ui_view WHERE id IN (
            SELECT res_id FROM ir_model_data
             WHERE module = 'tuv_audit_reports' AND name = 'edit_project_remove_audit_evidence_tab'
               AND model = 'ir.ui.view')
    """)
    cr.execute("""
        DELETE FROM ir_model_data
         WHERE module = 'tuv_audit_reports' AND name = 'edit_project_remove_audit_evidence_tab'
    """)
