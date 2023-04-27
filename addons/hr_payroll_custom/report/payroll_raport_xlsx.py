# -*- coding:utf-8 -*-

import datetime
from odoo import models, api, _


class HrPayrollPayrollXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_custom.hr_payroll_xlsx'
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

    content_format = {
        'bold': 0,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    amount_format = {
        'bold': 1,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '### ### ##0'
    }

    def formatSheet(self, sheet):
        sheet.set_column('A:A', 40)
        sheet.set_column('B:V', 15)

    def generateHeaders(self, sheet, headers, header_format):
        i = 2
        col = 1
        sheet.set_row(i, 30)
        sheet.write(i, 0, "Matricule", header_format)
        for code in headers:
            sheet.write(i, col, code, header_format)
            col += 1
        col += 1
        i += 1

    def generateLines(self, sheet, lines, codes, totaux, amount_format, content_format):
        i = 4
        for line in lines:
            col = 1
            sheet.write(i, 0, line['MATRICULE'], content_format)
            sheet.write(i, 1, line['NAME'], content_format)
            for code in codes:
                col += 1
                sheet.write(i, col, line[code], amount_format)
            i += 1
            sheet.write(i, 2, 'TOTAUX', content_format)
            sheet.write(i, col, totaux[code], amount_format)
            col += 1


    # def generateLinesTotaux(self, sheet, totaux, codes, amount_format, content_format):
    #     i = 6
    #     col = 0
    #     sheet.write(i, col, 'TOTAUX', content_format)
    #     col += 1
    #     for code in codes:
    #         col += 1
    #         sheet.write(i, col, totaux[code], amount_format)
    #     i += 1

    def generate_xlsx_report(self, workbook, data, lines):
        report_payroll_obj = self.env['report.hr_payroll_custom.report_payroll']
        # results = report_payroll_obj._lines(data['form']['date_from'], data['form']['date_to'], data['form']['company_id'])
        results = report_payroll_obj._lines(data['form']['date_from'], data['form']['date_to'],
                                            data['form']['company_id'],
                                            data['form']['type_employe'])
        totaux = report_payroll_obj._lines_total(results['codes'], results['lines'])

        sheet = workbook.add_worksheet('LIVRE DE PAIE')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.header_format)
        content_format = workbook.add_format(self.content_format)
        amount_format = workbook.add_format(self.amount_format)
        # self.formatSheet(sheet)
        title = data['form']['name']
        sheet.write(0, 0, title, bold)
        self.formatSheet(sheet)
        i = 3
        self.generateHeaders(sheet, results['headers'], header_format)
        self.generateLines(sheet, results['lines'], results['codes'],totaux, amount_format, content_format)
        # self.generateLinesTotaux(sheet, totaux, results['codes'], amount_format, content_format)

# HrPayrollPayrollXlsx('report.hr_payroll_ci_raport.hr_payroll.xlsx', 'hr.payroll.payroll')
