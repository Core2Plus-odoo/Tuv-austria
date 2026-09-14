{
    'name': "Dashboard-Business Insurance",

    'summary': "TUV Austria BIC client dashboard - where the certification business stands at a glance",

    'description': """
Dashboard-Business Insurance
============================
The opening screen of TUV Austria Bureau of Inspection & Certification.

It answers the first question anyone asks in the morning: *who are our clients and
where are they*. The client base from Contacts is broken down city by city and
country by country, each with a share bar, so the concentration of the business is
visible without opening a single list. Every bar is clickable and lands on exactly
those contacts.
""",

    'author': "Core2Plus",
    'website': "https://www.core2plus.com",
    'category': 'Services/Certification',
    'version': '1.0',

    'depends': ['base', 'web', 'contacts'],

    'data': [
        'views/tuv_dashboard_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'tuv_austria_dashboard/static/src/scss/tuv_dashboard.scss',
            'tuv_austria_dashboard/static/src/js/tuv_dashboard.js',
            'tuv_austria_dashboard/static/src/xml/tuv_dashboard.xml',
        ],
    },

    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
