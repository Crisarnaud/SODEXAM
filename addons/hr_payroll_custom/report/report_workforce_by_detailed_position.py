# -*- coding:utf-8 -*-

import datetime
from odoo import models, api, _


class WorkforceByDetailedPosition(models.AbstractModel):
    _name = 'report.hr_payroll_custom.workforce_by_detailed_position_xls'
    _inherit = 'report.report_xlsx.abstract'

    i = 0
    header_format = {
        'bold': 0,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#dddddd',
        'color': 'black',
        'text_wrap': 1,
        'font_name': 'Calibri',
        'font_size': 13,
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
        sheet.set_default_row(25)
        sheet.set_column('A:A', 35)
        sheet.set_column('B:D', 15)

    def generate_header(self, sheet, header, header_format):
        line = self.i + 1
        sheet.merge_range("A1:B1", 'Effectif par position détaillée', header_format)
        for head in header:
            sheet.merge_range("B3:D3", head, header_format)
            sheet.write(line + 2, 1, 'F', header_format)
            sheet.write(line + 2, 2, 'H', header_format)
            sheet.write(line + 2, 3, 'TOTAL', header_format)
        line += 3
        self.i = line

    def generateLines(self, sheet, data, content_label_format, content_number_format, cumul_label_format,
                      cumul_number_format):
        line = self.i

        cumul_female = 0
        cumul_male = 0
        for job in data:
            col = 0
            sheet.write(line, col, job['job'], content_label_format)
            sheet.write(line, col + 1, job['female'], content_number_format)
            cumul_female += job['female']
            sheet.write(line, col + 2, job['male'], content_number_format)
            cumul_male += job['male']
            sheet.write(line, col + 3, job['male'] + job['female'], cumul_number_format)
            line += 1
        sheet.write(line, 0, 'TOTAL', cumul_label_format)
        sheet.write(line, 1, cumul_female, cumul_number_format)
        sheet.write(line, 2, cumul_male, cumul_number_format)
        sheet.write(line, 3, cumul_male + cumul_female, cumul_number_format)
        self.i = line + 1

    def generate_xlsx_report(self, workbook, datas, obj):
        header = datas['header']
        data = datas['lines']
        sheet = workbook.add_worksheet('Effectif par position détaillée')
        header_format = workbook.add_format(self.header_format)
        content_label_format = workbook.add_format(self.content_label_format)
        content_number_format = workbook.add_format(self.content_number_format)
        cumul_label_format = workbook.add_format(self.cumul_label_format)
        cumul_number_format = workbook.add_format(self.cumul_number_format)
        self.formatSheet(sheet)
        self.generate_header(sheet, header, header_format)
        self.generateLines(sheet, data, content_label_format, content_number_format, cumul_label_format,
                           cumul_number_format)
        workbook.close()
