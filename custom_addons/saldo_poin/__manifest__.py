{
    'name': 'Saldo Poin',
    'version': '1.0',
    'summary': 'Halaman Saldo Poin untuk Member Program Referral',
    'category': 'Sales',
    'depends': ['base', 'web', 'referral_dashboard'],
    'data': [
        'security/ir.model.access.csv',
        'views/saldo_poin_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'saldo_poin/static/src/css/saldo_poin.css',
            'saldo_poin/static/src/js/saldo_poin.js',
            'saldo_poin/static/src/xml/saldo_poin.xml',
        ],
    },
    'installable': True,
    'application': True,
}
