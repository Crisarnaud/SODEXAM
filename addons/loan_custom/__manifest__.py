##############################################################################
#
# Copyright (c) 2012 Veone - support.veone.net
# Author: Veone
#
# Fichier du module hr_emprunt
# ##############################################################################
{
    "name": "LOAN CUSTOM",
    "version": "1.0",
    "author": "VEONE",
    "category": "Generic Modules/Human Resources",
    "website": "www.veone.net",
    "depends": ['hr', 'mail', 'hr_payroll', 'hr_payroll_custom', "hr_contract"],
    "description": """ Module permettant de gérer les emprunts des employés (Echeanciers, Remboursement, interfaçage 
    avec le module de paie)
    """,
    "init_xml": [],
    "demo_xml": [],
    "data": [
        "security/ir.model.access.csv",
        "data/data_sequence.xml",
        "report/report_loan.xml",
        "report/report.xml",
        "wizard/loaning_request_wizard_view.xml",
        "views/advance_salary_view.xml",
        "views/loaning_request_view.xml",
        "views/loaning_menu.xml",
    ],
    "installable": True
}
