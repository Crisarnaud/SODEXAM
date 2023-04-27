# -*- coding: utf-8 -*-
{
    'name': 'Hospital Management System for aeronautics',
    'version': '1.0.1',
    'summary': 'Hospital Management System for aeronautics',
    'description': """ """,
    'category': 'Medical',
    'author': 'Veone.',
    'support': '',
    'website': 'https://www.veone.net',
    'license': 'OPL-1',
    'depends': ['acs_hms_custom'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/hms_base_view.xml',
        'wizard/laboratory_wizard_view.xml',
        'views/laboratory_view.xml',
        'views/appointment_view.xml',
        'views/menu_item.xml',

    ],
    'images': [
    ],
    'installable': True,
    'application': True,
}
