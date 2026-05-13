{
    'name': 'Referral Analytics Dashboard',
    'version': '1.0',
    'summary': 'Tampilan Dashboard Analitik & Kebijakan Referral',
    'category': 'Sales',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_action.xml',
        'views/referral_policy_views.xml', 
    ],
    'assets': {
        'web.assets_backend': [
            'referral_dashboard/static/src/js/dashboard.js',
            'referral_dashboard/static/src/xml/dashboard.xml',
            'referral_dashboard/static/src/js/policy.js',
            'referral_dashboard/static/src/xml/policy.xml',
        ],
    },
    'installable': True,
    'application': True,
}