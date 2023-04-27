# -*- coding:utf-8 -*-

import datetime
from odoo import models, api, _


class HrPayrollByPosition(models.AbstractModel):
    _name = 'report.hr_payroll_custom.agent_payments_xls'
    _inherit = 'report.report_xlsx.abstract'

    header_format = {
        'bold': 0,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#dddddd',
        'color': 'black',
        'text_wrap': 1,
        'font_name': 'Calibri',
        'font_size': 13
    }

    content_label_format = {
        'bold': 0,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'color': 'black',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    content_number_format = {
        'bold': 0,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'color': 'black',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    cumul_label_format = {
        'bold': 1,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'color': 'black',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    cumul_number_format = {
        'bold': 1,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'color': 'black',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    def formatSheet(self, sheet):
        sheet.set_default_row(16)
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 45)
        sheet.set_column('C:BZ', 15)

    def generate_header(self, sheet, header, date_from, date_to, header_format):
        i = 0
        line = i + 1
        sheet.merge_range("A1:B1", 'Etat des payements par agent', header_format)
        sheet.write(line + 1, 0, 'Période', header_format)
        sheet.write(line + 1, 1, date_from, header_format)
        sheet.write(line + 1, 2, '-', header_format)
        sheet.write(line + 1, 3, date_to, header_format)
        sheet.write(line + 3, 0, 'Matricule', header_format)
        sheet.write(line + 3, 1, 'Employés', header_format)
        sheet.write_row(line + 3, 2, header, header_format)
        sheet.write(line + 3, len(header) + 2, 'Cumul employé', header_format)
        line += 4
        i = line

    def generateLines(self, sheet, header, data, content_label_format, content_number_format, cumul_label_format,
                      cumul_number_format):
        i = 0
        line = i
        list_rules = {}
        for head in header:
            list_rules[head] = 0
        cumul_row = 0
        for empoloyee in data:
            col = 0
            sheet.write(line, col, empoloyee['identification'], content_label_format)
            sheet.write(line, col+1, empoloyee['employee'], content_label_format)
            total_row = 0
            for rule in empoloyee['rules']:
                sheet.write(line, col + 2, rule['amount'], content_number_format)
                total_row += rule['amount']
                list_rules[rule['rule']] += rule['amount']
                col += 1
            cumul_row += total_row
            sheet.write(line, col + 2, total_row, cumul_number_format)
            line += 1
        cel_merge = 'A'+str(line+1)+':B'+str(line+1)
        sheet.merge_range(cel_merge, 'Cumul Total', cumul_label_format)
        col = 2
        for head in header:
            sheet.write(line, col, list_rules[head], cumul_number_format)
            col += 1
        sheet.write(line, col, cumul_row, cumul_number_format)
        i = line

    def generate_xlsx_report(self, workbook, datas, obj):
        data = datas['lines']
        header = datas['header']
        date_from = datas['date_from']
        date_to = datas['date_to']
        sheet = workbook.add_worksheet('Payement par agent')
        header_format = workbook.add_format(self.header_format)
        content_label_format = workbook.add_format(self.content_label_format)
        content_number_format = workbook.add_format(self.content_number_format)
        cumul_label_format = workbook.add_format(self.cumul_label_format)
        cumul_number_format = workbook.add_format(self.cumul_number_format)
        self.formatSheet(sheet)
        self.generate_header(sheet, header, date_from, date_to, header_format)
        self.generateLines(sheet, header, data, content_label_format, content_number_format, cumul_label_format,
                           cumul_number_format)
        workbook.close()
