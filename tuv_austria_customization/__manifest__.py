{
    'name': "TUV Austria Customization",

    'summary': "Custom changes to Sales, Contacts, Project and Inventory",

    'description': """
Custom Operations
==================
Centralized module for client-specific customizations across:
- Sales (sale.order)
- Contacts (res.partner)
- Project (project.project / project.task)
- Inventory (stock)
""",

    'author': "Core2Plus",
    'website': "https://www.core2plus.com",

    'category': 'Customizations',
    'version': '1.0',

    'depends': ['base', 'account', 'sale', 'sale_project', 'contacts', 'project', 'stock'],

    'data': [
        'security/ir.model.access.csv',
        'views/industry_ea_code_views.xml',
        'views/employment_type_views.xml',
        'views/certification_standard_views.xml',
        'views/auditor_category_views.xml',
        'views/service_category_views.xml',
        'views/unit_of_billing_views.xml',
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/project_views.xml',
        'views/project_task_mandays_views.xml',
        'views/stock_views.xml',
        'report/sale_order_application_form_report.xml',
        'report/sale_order_proposal_report.xml',
        'report/account_move_commercial_invoice_report.xml',
        'report/sale_order_contract_body.xml',
        'report/sale_order_contract_tac_tah_report.xml',
        'report/sale_order_contract_pnac_report.xml',
        'report/project_task_mandays_report.xml',
    ],

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
