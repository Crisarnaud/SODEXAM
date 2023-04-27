# -*- coding:utf-8 -*-

import datetime
from odoo import models, api, _
import xlsxwriter


class HrPayrollByPosition(models.AbstractModel):
    _name = 'report.hr_payroll_custom.payroll_by_period'
    _inherit = 'report.report_xlsx.abstract'

    # Formatage pour les headers
    header_format = {
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'white',
        'text_wrap': 1,
        'font_name': 'Calibri',
        'font_size': 16
    }

    sub_header_format = {
        'bold': 0,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'white',
        'text_wrap': 1,
        'font_name': 'Calibri',
        'font_size': 13
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
        'num_format': '### ### ### ### ##0'
    }
    sub_amount_format = {
        'bold': 0,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '### ### ##0'
    }

    total_format = {
        'bold': 1,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'fg_color': 'white',
        'text_wrap': 1,
        'font_name': 'Calibri',
        'font_size': 13
    }

    sum_employee_base = 0
    sum_employee_earnings = 0
    sum_employee_deductions = 0

    sum_employer_base = 0
    sum_employer_earnings = 0
    sum_employer_deductions = 0
    sum_employee_employer = 0

    def formatSheet(self, sheet):
        sheet.set_default_row(16)
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 33)
        sheet.set_column('C:H', 15)
        sheet.set_column('I:I', 20)

    def generateHeaders(self, sheet, date_from, date_to, header_format, sub_header_format):
        sheet.merge_range('A1:B1', 'CUMUL DES RUBRIQUES', header_format)
        sheet.write(0, 3, 'Période :', sub_header_format)
        sheet.write(0, 4, date_from, sub_header_format)
        sheet.write(0, 5, ' - ', sub_header_format)
        sheet.write(0, 6, date_to, sub_header_format)
        sheet.merge_range('C3:E3', 'SALARIALES', sub_header_format)
        sheet.merge_range('F3:H3', 'PATRONALES', sub_header_format)
        sheet.merge_range('I3:I4', 'SALARIALES + PATRONALES', sub_header_format)
        sheet.write(3, 0, 'Rubrique', sub_header_format)
        sheet.write(3, 1, 'Libelle Rubrique', sub_header_format)
        sheet.write(3, 2, 'Base', sub_header_format)
        sheet.write(3, 3, 'Gain', sub_header_format)
        sheet.write(3, 4, 'Retenue', sub_header_format)
        sheet.write(3, 5, 'Base', sub_header_format)
        sheet.write(3, 6, 'Gain', sub_header_format)
        sheet.write(3, 7, 'Retenue', sub_header_format)

    def generateLines(self, sheet, data, content_format, sub_amount_format):
        sum_employee_employer = 0

        line = 4
        for rec in data:
            sum_of_row = 0
            sheet.write(line, 0, rec['sequence'] or '', content_format)
            sheet.write(line, 1, rec['rule_name'], content_format)
            sheet.write(line, 2, '', content_format)
            sheet.write(line, 3, '', content_format)
            sheet.write(line, 4, '', content_format)
            sheet.write(line, 5, '', content_format)
            sheet.write(line, 6, '', content_format)
            sheet.write(line, 7, '', content_format)
            if rec['type'] == 'employee':
                sheet.write(line, 2, rec['base'], sub_amount_format)
                self.sum_employee_base += rec['base']
                if rec['imputation_type'] == 'earnings':
                    sheet.write(line, 3, rec['amount'], sub_amount_format)
                    sum_of_row += rec['amount']
                    self.sum_employee_earnings += rec['amount']
                if rec['imputation_type'] == 'deductions':
                    sheet.write(line, 4, rec['amount'], sub_amount_format)
                    sum_of_row += rec['amount']
                    self.sum_employee_deductions += rec['amount']
            if rec['type'] == 'employer':
                sheet.write(line, 5, rec['base'], sub_amount_format)
                self.sum_employer_base += rec['base']
                if rec['imputation_type'] == 'earnings':
                    sheet.write(line, 6, rec['amount'], sub_amount_format)
                    sum_of_row += rec['amount']
                    self.sum_employer_earnings += rec['amount']
                if rec['imputation_type'] == 'deductions':
                    sheet.write(line, 7, rec['amount'], sub_amount_format)
                    sum_of_row += rec['amount']
                    self.sum_employer_deductions += rec['amount']
            sheet.write(line, 8, sum_of_row, sub_amount_format)
            sum_employee_employer += sum_of_row
            line += 1


    def generateLinesTotaux(self, sheet, amount_format, total_format):
        sum_employee_employer = 0
        i = 10
        col = 1
        sheet.write(i, col, 'TOTAL GENERAL', total_format)
        sheet.write(i, col + 1, self.sum_employee_base, amount_format)
        sheet.write(i, col + 2, self.sum_employee_earnings, amount_format)
        sheet.write(i, col + 3, self.sum_employee_deductions, amount_format)
        sheet.write(i, col + 4, self.sum_employer_base, amount_format)
        sheet.write(i, col + 5, self.sum_employer_earnings, amount_format)
        sheet.write(i, col + 6, self.sum_employer_deductions, amount_format)
        sheet.write(i, col + 7, sum_employee_employer, amount_format)

    def generate_xlsx_report(self, workbook, datas, obj):
        data = datas['lines']

        date_from = datas['date_from']
        date_to = datas['date_to']
        sheet = workbook.add_worksheet('Cumul des rubriques par période')
        header_format = workbook.add_format(self.header_format)
        sub_header_format = workbook.add_format(self.sub_header_format)
        content_format = workbook.add_format(self.content_format)
        amount_format = workbook.add_format(self.amount_format)
        sub_amount_format = workbook.add_format(self.sub_amount_format)
        total_format = workbook.add_format(self.total_format)
        self.formatSheet(sheet)
        self.generateHeaders(sheet, date_from, date_to, header_format, sub_header_format)
        self.generateLines(sheet, data, content_format, sub_amount_format)
        self.generateLinesTotaux(sheet, amount_format, total_format)
        workbook.close()
