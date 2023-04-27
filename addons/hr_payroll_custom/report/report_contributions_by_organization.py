# -*- coding:utf-8 -*-

import datetime
from odoo import models, api, _


class HrPayrollByPosition(models.AbstractModel):
    _name = 'report.hr_payroll_custom.contribution_by_organization'
    _inherit = 'report.report_xlsx.abstract'

    tax_contribution_format = {
        'bold': 0,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#00b050',
        'color': 'white',
        'text_wrap': 1,
        'font_name': 'Calibri',
        'font_size': 13
    }

    social_contribution_format = {
        'bold': 0,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#ff0000',
        'color': 'white',
        'text_wrap': 1,
        'font_name': 'Calibri',
        'font_size': 13
    }

    contribution_by_organization_format = {
        'bold': 0,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'black',
        'color': 'white',
        'text_wrap': 1,
        'font_name': 'Calibri',
        'font_size': 13
    }

    content_label_format = {
        'bold': 0,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'color': '#0070c0',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    content_number_format = {
        'bold': 0,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'color': '#0070c0',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    cumul_label_format = {
        'bold': 0,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'color': 'black',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    cumul_number_format = {
        'bold': 0,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'color': 'black',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    def formatSheet(self, sheet):
        sheet.set_default_row(16)
        sheet.set_column('A:A', 45)
        sheet.set_column('B:Z', 33)

    def generateLines(self, sheet, months, data, content_label_format, content_number_format, tax_contribution_format,
                      social_contribution_format, contribution_by_organization_format, cumul_label_format,
                           cumul_number_format):
        i = 0
        line = 2
        sheet.write(line - 1, 0, 'COTISATION FISCALE SALARIALE', tax_contribution_format)
        sheet.write_row(line - 1, 1, months, tax_contribution_format)
        list_month = {}
        for month in months:
            list_month[month] = 0
        cumul_row = 0
        for rec in data:
            if rec['category_type'] == 'employee' and rec['contribution_type'] == 'tax':
                sheet.write(line, 0, rec['rule_name'] or '', content_label_format)
                col = 1
                total_row = 0
                for mt in rec['month_amount']:
                    sheet.write(line, col, mt['amount'], content_number_format)
                    total_row += mt['amount']
                    list_month[mt['month']] += mt['amount']
                    col += 1
                cumul_row += total_row
                sheet.write(line, col, total_row, content_number_format)
                line += 1
        sheet.write(line, 0, 'Cumul mensuel', cumul_label_format)
        col = 1
        for month in months:
            sheet.write(line, col, list_month[month], cumul_number_format)
            col += 1
        sheet.write(line, col - 1, cumul_row, cumul_number_format)

        list_month = {}
        for month in months:
            list_month[month] = 0
        line += 4
        sheet.write(line - 1, 0, 'COTISATION FISCALE PATRONALE', tax_contribution_format)
        sheet.write_row(line - 1, 1, months, tax_contribution_format)
        cumul_row = 0
        for rec in data:
            if rec['category_type'] == 'employer' and rec['contribution_type'] == 'tax':
                sheet.write(line, 0, rec['rule_name'] or '', content_label_format)
                col = 1
                total_row = 0
                for mt in rec['month_amount']:
                    sheet.write(line, col, mt['amount'], content_number_format)
                    total_row += mt['amount']
                    list_month[mt['month']] += mt['amount']
                    col += 1
                cumul_row += total_row
                sheet.write(line, col, total_row, content_number_format)
                line += 1
            sheet.write(line, 0, 'Cumul mensuel', cumul_label_format)
            col = 1
            for month in months:
                sheet.write(line, col, list_month[month], cumul_number_format)
                col += 1
            sheet.write(line, col - 1, cumul_row, cumul_number_format)

        list_month = {}
        for month in months:
            list_month[month] = 0
        line += 4
        sheet.write(line - 1, 0, 'COTISATIONS SOCIALES SALARIALES', social_contribution_format)
        sheet.write_row(line - 1, 1, months, social_contribution_format)
        cumul_row = 0
        for rec in data:
            if rec['category_type'] == 'employee' and rec['contribution_type'] == 'social':
                sheet.write(line, 0, rec['rule_name'] or '', content_label_format)
                col = 1
                total_row = 0
                for mt in rec['month_amount']:
                    sheet.write(line, col, mt['amount'], content_number_format)
                    total_row += mt['amount']
                    list_month[mt['month']] += mt['amount']
                    col += 1
                cumul_row += total_row
                sheet.write(line, col, total_row, content_number_format)
                line += 1
            sheet.write(line, 0, 'Cumul mensuel', cumul_label_format)
            col = 1
            for month in months:
                sheet.write(line, col, list_month[month], cumul_number_format)
                col += 1
            sheet.write(line, col - 1, cumul_row, cumul_number_format)

        list_month = {}
        for month in months:
            list_month[month] = 0
        line += 4
        sheet.write(line - 1, 0, 'COTISATIONS SOCIALES PATRONALES', social_contribution_format)
        sheet.write_row(line - 1, 1, months, social_contribution_format)
        cumul_row = 0
        for rec in data:
            if rec['category_type'] == 'employer' and rec['contribution_type'] == 'social':
                sheet.write(line, 0, rec['rule_name'] or '', content_label_format)
                col = 1
                total_row = 0
                for mt in rec['month_amount']:
                    sheet.write(line, col, mt['amount'], content_number_format)
                    total_row += mt['amount']
                    list_month[mt['month']] += mt['amount']
                    col += 1
                cumul_row += total_row
                sheet.write(line, col, total_row, content_number_format)
                line += 1
            sheet.write(line, 0, 'Cumul mensuel', cumul_label_format)
            col = 1
            for month in months:
                sheet.write(line, col, list_month[month], cumul_number_format)
                col += 1
            sheet.write(line, col - 1, cumul_row, cumul_number_format)

        list_month = {}
        for month in months:
            list_month[month] = 0
        line += 4
        sheet.write(line - 1, 0, 'ETAT COTISATIONS PAR ORGANISME DETAILLE', contribution_by_organization_format)
        sheet.write_row(line - 1, 1, months, contribution_by_organization_format)
        total_amount = 0
        cumul_row = 0
        for rec in data:
            if rec['category_type'] == 'employee' and rec['contribution_type'] == 'tax':
                sheet.write(line, 0, rec['rule_name'] or '', content_label_format)
                col = 1
                total_row = 0
                for mt in rec['month_amount']:
                    sheet.write(line, col, mt['amount'], content_number_format)
                    total_amount += mt['amount']
                    total_row += mt['amount']
                    list_month[mt['month']] += mt['amount']
                    col += 1
                cumul_row += total_row
                sheet.write(line, col, total_row, content_number_format)
                line += 1
        for rec in data:
            if rec['category_type'] == 'employer' and rec['contribution_type'] == 'tax':
                sheet.write(line, 0, rec['rule_name'] or '', content_label_format)
                col = 1
                total_row = 0
                for mt in rec['month_amount']:
                    sheet.write(line, col, mt['amount'], content_number_format)
                    total_amount += mt['amount']
                    total_row += mt['amount']
                    list_month[mt['month']] += mt['amount']
                    col += 1
                cumul_row += total_row
                sheet.write(line, col, total_row, content_number_format)
                line += 1
        for rec in data:
            if rec['category_type'] == 'employee' and rec['contribution_type'] == 'social':
                sheet.write(line, 0, rec['rule_name'] or '', content_label_format)
                col = 1
                total_row = 0
                for mt in rec['month_amount']:
                    sheet.write(line, col, mt['amount'], content_number_format)
                    total_amount += mt['amount']
                    total_row += mt['amount']
                    list_month[mt['month']] += mt['amount']
                    col += 1
                cumul_row += total_row
                sheet.write(line, col, total_row, content_number_format)
                line += 1
        for rec in data:
            if rec['category_type'] == 'employer' and rec['contribution_type'] == 'social':
                sheet.write(line, 0, rec['rule_name'] or '', content_label_format)
                col = 1
                total_row = 0
                for mt in rec['month_amount']:
                    sheet.write(line, col, mt['amount'], content_number_format)
                    total_amount += mt['amount']
                    total_row += mt['amount']
                    list_month[mt['month']] += mt['amount']
                    col += 1
                cumul_row += total_row
                sheet.write(line, col, total_row, content_number_format)
                line += 1
        sheet.write(line, 0, 'Cumul mensuel', cumul_label_format)
        col = 1
        for month in months:
            sheet.write(line, col, list_month[month], cumul_number_format)
            col += 1
        sheet.write(line, col - 1, cumul_row, cumul_number_format)
        i = line

    def generate_xlsx_report(self, workbook, datas, obj):
        data = datas['lines']
        months = datas['months']
        sheet = workbook.add_worksheet('Cotisations par organisme')
        tax_contribution_format = workbook.add_format(self.tax_contribution_format)
        social_contribution_format = workbook.add_format(self.social_contribution_format)
        contribution_by_organization_format = workbook.add_format(self.contribution_by_organization_format)
        content_label_format = workbook.add_format(self.content_label_format)
        content_number_format = workbook.add_format(self.content_number_format)

        cumul_label_format = workbook.add_format(self.cumul_label_format)
        cumul_number_format = workbook.add_format(self.cumul_number_format)
        self.formatSheet(sheet)
        self.generateLines(sheet, months, data, content_label_format, content_number_format, tax_contribution_format,
                           social_contribution_format, contribution_by_organization_format, cumul_label_format,
                           cumul_number_format)
        workbook.close()
