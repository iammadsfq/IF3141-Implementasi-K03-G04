{
    'name': 'Referral Analytics Dashboard',
    'version': '17.0.1.0.0',
    'summary': 'Tampilan Dashboard Analitik dan Kebijakan Referral PT Nomar Kopi',
    'category': 'Sales',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'referral_registration'],
    'data': [
        'security/ir.model.access.csv',
        'data/referral_policy_data.xml',
        'views/dashboard_action.xml',
        'views/referral_policy_views.xml',
        'views/referral_transaction_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'referral_dashboard/static/src/css/referraL_dashboard.css',
            'referral_dashboard/static/src/xml/dashboard.xml',
            'referral_dashboard/static/src/xml/policy.xml',
            'referral_dashboard/static/src/js/dashboard.js',
            'referral_dashboard/static/src/js/policy.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
