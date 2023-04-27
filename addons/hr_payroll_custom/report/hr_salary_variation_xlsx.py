# -*- coding:utf-8 -*-

import datetime
from odoo import models, api, _


class HrSalaryVariation(models.AbstractModel):
    _name = 'report.hr_payroll_custom.report_hr_salary_variation'
    _inherit = 'report.report_xlsx.abstract'

    # Formattage pour les headers
    header_format = {
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'gray',
        'text_wrap': 1
    }

    string_format = {
        'bold': 0,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'fg_color': 'white',
    }

    content_format = {
        'bold': 0,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    amount_format = {
        'bold': 1,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '# ##0'
    }

    def formatSheet(self, sheet):
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 12)
        sheet.set_column('C:C', 50)

    def generateHeaders(self, sheet, headers, header_format):
        i = 0
        sheet.set_row(i, 30)
        sheet.merge_range(i, 0, i + 1, 0, 'N°', header_format)
        sheet.merge_range(i, 1, i + 1, 1, 'Matricule', header_format)
        sheet.merge_range(i, 2, i + 1, 2, 'NOM ET PRENOMS', header_format)
        idx1 = 3
        idx2 = 6
        for key in headers.keys():
            sheet.merge_range(i, idx1, i, idx2, headers[key], header_format)
            idx1 = idx2 + 1
            idx2 += 4
        i += 1
        col = 3
        for key in headers.keys():
            sheet.write(i, col, 'Ancien', header_format)
            sheet.write(i, col + 1, 'Nouveau', header_format)
            sheet.write(i, col + 2, 'Ecart', header_format)
            sheet.write(i, col + 3, 'Observation', header_format)
            sheet.set_column(i, col, 10)
            sheet.set_column(i, col + 1, 10)
            sheet.set_column(i, col + 2, 10)
            sheet.set_column(i, col + 3, 14)
            col += 4
        i += 1

    def generateLines(self, sheet, elements, codes, string_format):
        number = 1
        i = 2
        for elt in elements:
            col = 0
            sheet.write(i, col, number, string_format)
            sheet.write(i, col + 1, elt['matricule'], string_format)
            sheet.write(i, col + 2, elt['name'] + ' ' + elt['first_name'], string_format)
            col += 3
            line = elt['line']
            old_line = elt['old_line']
            for key in codes.keys():
                sheet.write(i, col, old_line[key], string_format)
                col += 1
                sheet.write(i, col, line[key], string_format)
                col += 1
                ecart = line[key] - old_line[key]
                sheet.write(i, col, ecart, string_format)
                col += 1
                sheet.write(i, col, '', string_format)
                col += 1
            i += 1
            number += 1

    def generate_xlsx_report(self, workbook, data, obj):
        codes = obj.getCodes()
        obj.getOldPeriodes()
        old_lines = obj.getpayslipLinesForPeriode(codes, obj.old_date_from, obj.old_date_to)

        new_lines = obj.getpayslipLinesForPeriode(codes, obj.date_from, obj.date_to)
        employee_ids = obj.getEmployeePeriode()

        elements = obj.compute_data(employee_ids, new_lines, old_lines, codes)

        sheet = workbook.add_worksheet('RECAPITULATIF DES SALAIRES / EMPLOYE')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.header_format)
        # _content_format = workbook.add_format(self.content_format)
        string_format = workbook.add_format(self.string_format)
        amount_format = workbook.add_format(self.amount_format)
        self.formatSheet(sheet)
        i = 3
        self.generateHeaders(sheet, codes, header_format)
        self.generateLines(sheet, elements, codes, string_format)
