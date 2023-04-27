# -*- coding:utf-8 -*-

import datetime

from odoo import models


class HrPayrollPayrollWizardXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_custom.cnps_mensuel_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    i = 0

    title = ['NUMERO CNPS', 'NOM', 'PRENOMS', 'ANNEE DE NAISSANCE', "DATE D'EMBAUCHE", "DATE DE DEPART",
             'TYPE SALARIE M: Mensuel J : Journalier '
             'H: Horaire', 'DUREE TRAVAILLEE', 'SALAIRE BRUT']

    # Formattage pour les headers
    h_format = {
        'bold': 1,
        'border': 1,
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'gray',
        'text_wrap': 1
    }

    c_format = {
        'bold': 0,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'white'
    }

    a_format = {
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '# ##0'
    }

    a_total_format = {
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '# ##0',
        'fg_color': 'gray',
    }

    def formatSheet(self, sheet):
        sheet.set_row(0, 50)
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 40)
        sheet.set_column('H:H', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('L:L', 30)
        sheet.set_column('N:N', 30)
        sheet.set_column('D:ZZ', 15)

    def generateLines(self, sheet, obj, content_format, header_format, amount_format):
        row = 1
        brut_tot = []
        for line in obj.other_line_ids:
            brut_tot.append(line.amount_brut)
            sheet.write(row, 0, line.employee_id.identification_cnps if line.employee_id.identification_cnps else '',
                        content_format)
            sheet.write(row, 1, line.employee_id.name, content_format)
            sheet.write(row, 2, line.employee_id.first_name, content_format)
            sheet.write(row, 3, str(line.employee_id.birthday.year) if line.employee_id.birthday else '',
                        content_format)
            sheet.write(row, 4,
                        str(line.employee_id.start_date.strftime('%d/%m/%Y')) if line.employee_id.start_date else '',
                        content_format)
            sheet.write(row, 5,
                        str(line.employee_id.end_date.strftime('%d/%m/%Y')) if line.employee_id.end_date else '',
                        content_format)
            sheet.write(row, 6, line.employee_id.type.capitalize() if line.employee_id.type else '',
                        content_format)
            sheet.write(row, 7, 1, content_format)
            sheet.write(row, 8, line.amount_brut, content_format)
            row += 1

    def writeHeaders(self, sheet, obj, header_format):
        col = 0
        row = 0
        sheet.set_default_row(30)
        for i in range(len(self.title)):
            sheet.write(row, col, self.title[i], header_format)
            col += 1
        row += 1

    def generate_xlsx_report(self, workbook, data, obj):

        sheet = workbook.add_worksheet('Declaration annuelle de salaires')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.h_format)
        content_format = workbook.add_format(self.c_format)
        amount_format = workbook.add_format(self.a_format)
        amount_total_format = workbook.add_format(self.a_total_format)
        self.formatSheet(sheet)
        row = 0
        self.writeHeaders(sheet, obj, header_format)
        self.generateLines(sheet, obj, content_format, header_format, amount_format)
