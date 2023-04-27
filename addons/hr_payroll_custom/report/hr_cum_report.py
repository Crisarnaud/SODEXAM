# -*- coding:utf-8 -*-

import datetime
from odoo import models, api, _


class HrCMURapportXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_custom.cmu_rapport.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    # Formattage pour les headers
    header_format = {
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#afafaf',
        'text_wrap': 1
    }

    content_format_left = {
        'bold': 0,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'fg_color': 'white',
        'font_name': 'Helvetica'
    }
    content_format_right = {
        'bold': 0,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'fg_color': 'white',
        'font_name': 'Helvetica'
    }

    date_format = {
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': 'dd/mm/yyyy',
        'font_name': 'Helvetica'
    }

    headers = (
        "NUMERO CNPS \nASSURE",
        "NUMERO SECURITE\nSOCIALE ASSURE",
        "NOM ASSURE",
        "PRENOMS ASSURE",
        "DATE DE NAISSANCE\nASSURE",
        "NUMERO CNPS\nBENEFICIAIRE",
        "NUMERO SECURITE\nSOCIALE BENEFICIAIRE",
        "TYPE BENEFICIAIRE \nC: CONJOINT \nT: TRAVAILLEUR \nE: ENFANT",
        "NOM BENEFICIAIRE",
        "PRENOMS BENEFICIAIRE",
        "DATE DE NAISSANCE\nBENEFICIAIRE",
        "GENRE \nBENEFICIAIRE \nH: HOMME \nF: FEMME"
    )

    def formatSheet(self, sheet):
        sheet.set_column('A:B', 15)
        sheet.set_column('C:C', 35)
        sheet.set_column('D:D', 55)
        sheet.set_column('E:G', 15)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 35)
        sheet.set_column('J:J', 55)
        sheet.set_column('K:K', 15)
        sheet.set_column('L:L', 15)

    def generateHeaders(self, sheet, header_format):
        i = 0
        col = 0
        sheet.set_row(0, 70)
        for x in range(len(self.headers)):
            sheet.write(i, col, self.headers[x], header_format)
            col += 1
        i += 1

    def generateLines(self, sheet, lines, content_format_left, content_format_right, date_format):
        i = 1
        for line in lines:
            sexe = "H"
            sheet.write(i, 0, line.num_cnps or '', content_format_right)
            sheet.write(i, 1, line.num_cmu or '', content_format_left)
            sheet.write(i, 2, line.name.upper() if line.name else '', content_format_left)
            sheet.write(i, 3, line.first_name.upper() if line.first_name else '', content_format_left)
            sheet.write(i, 4, line.birthday or '', date_format)
            sheet.write(i, 5, line.num_cnps or '', content_format_right)
            sheet.write(i, 6, line.num_cmu_beneficiary or '', content_format_left)
            sheet.write(i, 7, str(line.type).upper(), content_format_left)
            sheet.write(i, 8, line.name_beneficiary.upper() if line.name_beneficiary else '', content_format_left)
            sheet.write(i, 9, line.first_name_beneficiary.upper() if line.first_name_beneficiary else '',
                        content_format_left)
            sheet.write(i, 10, line.birthday_beneficiary or '', date_format)
            if line.gender != 'male':
                sexe = "F"
            sheet.write(i, 11, sexe, content_format_left)
            i += 1

    def generate_xlsx_report(self, workbook, data, obj):
        sheet = workbook.add_worksheet('CMU')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.header_format)
        content_format_left = workbook.add_format(self.content_format_left)
        content_format_right = workbook.add_format(self.content_format_right)
        date_format = workbook.add_format(self.date_format)
        self.formatSheet(sheet)
        i = 0
        self.generateHeaders(sheet, header_format)
        if obj.line_ids:
            self.generateLines(sheet, obj.line_ids, content_format_left, content_format_right, date_format)
