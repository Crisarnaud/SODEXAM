{
    "name": "ACCOUNT SODEXAM ",
    "version": "1.0",
    "author": "VEONE",
    'category': 'Comptabilité',
    "website": "http://www.veone.net",
    "depends": ["hr_payroll_custom", "account", "account_accountant"],
    "description": """
    """,
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [

    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/account_custom_view.xml",
    ],
    "installable": True
}
