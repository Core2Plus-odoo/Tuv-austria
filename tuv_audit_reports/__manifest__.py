{
    'name': "Audit Reports",

    'summary': "Audit forms of TUV Austria filled in Odoo (Audit Plan FM-TAGMBH-MSZ-001)",

    'description': """
Audit Reports
=============
The audit forms of TUV Austria, kept as records in Odoo instead of Word files.

* Audit Plan (FM-TAGMBH-MSZ-001, revision 08/22.01.2026): company and audit
  information, audit standards, audit team, audit schedule, signatures.
""",

    'author': "Core2Plus",
    'website': "https://www.core2plus.com",
    'category': 'Services/Certification',
    'version': '1.0',

    'depends': ['base', 'project', 'tuv_austria_customization'],

    'data': [
        'security/ir.model.access.csv',
        'security/acc_audit_plans_security.xml',
        'security/acc_audit_reports_security.xml',
        'security/acc_small_forms_security.xml',
        'security/acc_aqg_checklists_security.xml',
        'views/audit_plan_views.xml',
        'views/audit_report_views.xml',
        'views/project_views.xml',
        'views/forms/audit_plan.xml',
        'views/forms/audit_plan_isms.xml',
        'views/forms/audit_checklist.xml',
        'views/forms/audit_checklist_isms.xml',
        'views/forms/audit_participation.xml',
        'views/forms/audit_expert_report.xml',
        'views/forms/audit_certificate_text.xml',
        'views/forms/audit_letters.xml',
        'views/forms/audit_report_form.xml',
        'views/forms/audit_documents.xml',
        'views/forms/acc_audit_plans.xml',
        'views/forms/acc_audit_reports.xml',
        'views/forms/acc_small_forms.xml',
        'views/forms/acc_aqg_checklists.xml',
        'views/standalone_blocks.xml',
        'report/common_templates.xml',
        'report/audit_plan_report.xml',
        'report/audit_plan_isms_report.xml',
        'report/audit_checklist_report.xml',
        'report/audit_checklist_isms_report.xml',
        'report/audit_participation_report.xml',
        'report/audit_expert_report.xml',
        'report/audit_certificate_text_report.xml',
        'report/audit_letters_report.xml',
        'report/audit_report_form_report.xml',
        'report/audit_documents_report.xml',
        'report/acc_audit_plans_report.xml',
        'report/acc_audit_reports_report.xml',
        'report/acc_small_forms_report.xml',
        'report/acc_aqg_checklists_report.xml',
        'views/menus.xml',
        'data/audit_report_data.xml',
        'data/audit_checklist_data.xml',
        'data/audit_forms_data.xml',
        'data/acc_reuse_data.xml',
        'data/acc_audit_plans_data.xml',
        'data/acc_audit_reports_data.xml',
        'data/acc_small_forms_data.xml',
        'data/acc_aqg_checklists_data.xml',
    ],

    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
