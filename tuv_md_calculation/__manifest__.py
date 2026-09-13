{
    'name': "MD's Calculation",

    'summary': "Man-day (person-day) calculation rules for every certification scheme",

    'description': """
MD's Calculation
================
The place where the audit man-day rules of TUV Austria BIC live.

Every certification scheme (ISO 9001, ISO 14001, ISO/IEC 20000-1, FSSC 22000 ...)
comes with its own annex to `VB-BA-ZET-MS-All-003` - an audit duration table plus the
factors that increase or decrease the audit time. Those annexes are captured here once,
so that a planning or project user only has to pick the scheme and the number of
effective personnel to get the audit days the standard prescribes.
""",

    'author': "Core2Plus",
    'website': "https://www.core2plus.com",
    'category': 'Services/Certification',
    'version': '1.0',

    'depends': ['base', 'mail'],

    'data': [
        'security/md_calculation_groups.xml',
        'security/ir.model.access.csv',
        'views/md_scheme_views.xml',
        'views/md_scheme_import_views.xml',
        'views/md_menus.xml',
        'data/md_scheme_iso_20000_data.xml',
        'data/md_scheme_annexes_data.xml',
    ],

    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
