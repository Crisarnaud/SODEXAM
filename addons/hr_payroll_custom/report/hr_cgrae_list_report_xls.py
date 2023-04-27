# -*- coding:utf-8 -*-

import datetime

from odoo import models


class HrListReport(models.AbstractModel):
    _name = "report.hr_payroll_custom.hr_cgrae_list_report_xls_1"
    _inherit = 'report.report_xlsx.abstract'

    i = 0

    title = ['N°Ordre', 'NOM ET PRENOMS', 'Matricule Fonction Publ.', 'Salaires bruts mensuels', "Cotisation Mensuel(8.33%)",
             "Cotisation Mensuel(16.67%)", 'Total Cotisation', "OBSERVATION"
             ]

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
        sheet.set_column('A:A', 11)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 17)
        sheet.set_column('D:D', 17)
        sheet.set_column('E:E', 17)
        sheet.set_column('F:F', 30)
        sheet.set_column('G:G', 30)
        sheet.set_column('H:ZZ', 15)

    def generateLines(self, sheet, obj, header_format, content_format, amount_format, amount_total_format):
        line = 1
        brut_tot = []
        amount_cgrae = []
        amount_cgrae_monthly = []
        amount_cot_total = []
        for line in obj.line_ids:
            brut_tot.append(line.amount_brut)
            amount_cgrae.append(line.amount_cgrae_employe)
            amount_cgrae_monthly.append(line.amount_cgrae_employer)
            amount_cot_total.append(line.amount_cotisation_total)
            sheet.write(line, 0, line.num_order, content_format)
            sheet.write(line, 1, line.employee_id.name, content_format)
            sheet.write(line, 2, line.employee_id.num_cgare, content_format)
            sheet.write(line, 3, line.amount_brut, content_format)
            sheet.write(line, 4, line.amount_cgrae_employe, content_format)
            sheet.write(line, 5, line.amount_cgrae_employer, content_format)
            sheet.write(line, 6, line.amount_cotisation_total, content_format)
            sheet.write(line, 7, line.observation, content_format)
            line += 1

            sheet.write(line, 3, sum(brut_tot), content_format)
            sheet.write(line, 4, sum(amount_cgrae), content_format)
            sheet.write(line, 5, sum(amount_cgrae_monthly), content_format)
            sheet.write(line, 6, sum(amount_cot_total), content_format)
            sheet.write(line, 7, '', content_format)
        sheet.merge_range(line, 0, line, 2, 'TOTAL', content_format)

    def writeHeaders(self, sheet, obj, header_format):
        col = 0
        line = 0
        sheet.set_default_row(30)
        for i in range(len(self.title)):
            sheet.write(line, col, self.title[i], header_format)
            col += 1
        line += 1

    def generate_xlsx_report(self, workbook, data, obj):
        # print(totaux)
        sheet = workbook.add_worksheet('DECLARATION UNIVERSELLE DES SALAIRES')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.h_format)
        content_format = workbook.add_format(self.c_format)
        amount_format = workbook.add_format(self.a_format)
        amount_total_format = workbook.add_format(self.a_total_format)
        self.formatSheet(sheet)
        line = 0
        self.writeHeaders(sheet, obj, header_format)
        self.generateLines(sheet, obj, header_format, content_format, amount_format, amount_total_format)
