# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Veone - support.veone.net
# Author: Veone
#
# Fichier du module hr_synthese
# ##############################################################################
{
    "name": "HR CONTRACT",
    "version": "1.0",
    "author": "VEONE Technologies",
    'category': 'Human Resources',
    "website": "www.veone.net",
    "depends": ['base', 'mail', 'hr_contract', 'hr_employee_custom'],
    "description": """ 
    Extension du contrats de travail des employés
    """,
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [

    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/template_email_alert_end_trial_contract.xml",
        "data/hr_contract_data.xml",
        "wizard/hr_contract_closed.xml",
        "wizard/hr_employee_report_wizard.xml",
        "wizard/import_prime.xml",
        "views/hr_category_employee_view.xml",
        "views/hr_category_salaire_view.xml",
        "views/res_config_settings_views.xml",
        "views/hr_contract_config_view.xml",
        "views/hr_contract_model_view.xml",
        "views/hr_contract_view.xml",
        "report/report_view.xml",
        "report/report_employee_pdf.xml",
        "report/report_templates.xml",
        "report/layout_report_employee.xml",
        "views/hr_contract_custom_menu.xml"
    ],
    "installable": True
}
