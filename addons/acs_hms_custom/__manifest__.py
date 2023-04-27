# -*- coding: utf-8 -*-
{
    'name': "SODEXAM CENTRE MEDICAL",

    'summary': """
        """,

    'description': """

    """,

    'author': "Veone technology",
    'website': "http://www.veone.net",
    'category': 'hms',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'acs_hms_base',
        'acs_hms',
        'resource',
        'account',
        'acs_hms_surgery',
        'acs_hms_hospitalization',
        'acs_hms_insurance',
        'acs_laboratory',
        'acs_hms_laboratory',
        'acs_hms_commission',
        'acs_commission',
    ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data_hms.xml',
        'views/hms_base_view.xml',
        'views/appointment_view.xml',
        'views/physician_view.xml',
        'views/res_company_view.xml',
        'views/commission_view.xml',
        'views/insurance_view.xml',
        'views/product_view.xml',
        'wizard/refused_raison_wizard.xml',
        'views/laboratory_view.xml',
        'views/account_move_view.xml',
        'views/treatment_view.xml',
        'views/menu_item.xml',
    ],
    # only loaded in demonstration mode
}
