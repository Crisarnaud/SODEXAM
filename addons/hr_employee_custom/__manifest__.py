{
    "name": "HR EMPLOYEE",
    "version": "1.0",
    "author": "VEONE",
    'category': 'Employee',
    "website": "http://www.veone.net",
    "depends": ["base", 'hr', 'hr_contract', 'mail', 'report_xlsx'],
    "description": """
    """,
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [

    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "data/hr_employee_view_data.xml",
        "views/hr_employee_config_view.xml",
        "views/hr_employee_view.xml",
        "views/res_company_view.xml",
        "views/hr_employee_custom_menu.xml",
        "reports/layout_view.xml",
        "reports/report_new_employee_pdf.xml",
        "reports/report_view.xml",
        "reports/report_attestation_travail.xml",
        "reports/report_employee_resignation_pdf.xml",
        "wizards/hr_employee_resignation_wizard.xml",
        "wizards/hr_new_employee_wizard.xml",

    ],
    "installable": True
}
