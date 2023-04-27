# -*- coding:utf-8 -*-

import datetime
from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)


class HrSalaryVariationByRule(models.AbstractModel):
    _name = 'report.hr_payroll_custom.report_hr_salary_variation_by_rule'
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
        'num_format': '### ### ##0'
    }

    def formatSheet(self, sheet):
        sheet.set_column(0, 5, 15)
        sheet.set_default_row(30)
        sheet.set_column('A:B', 10)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:E', 15)
        sheet.set_column('F:G', 50)

    def generateHeaders(self, sheet, header_format):
        i = 0
        sheet.set_row(i, 30)
        sheet.write(i, 0, 'RUBRIQUE', header_format)
        sheet.write(i, 1, 'LIBELLÉ RUBRIQUE', header_format)
        sheet.write(i, 2, 'MOIS PRÉCÉDENT', header_format)
        sheet.write(i, 3, 'MOIS EN COURS', header_format)
        sheet.write(i, 4, 'ECART', header_format)
        sheet.write(i, 5, 'OBSERVATION', header_format)
        i += 1

    def generateLines(self, sheet, elements, string_format, content_format, amount_format):
        i = 1
        for elt in elements:
            col = 0
            sheet.write(i, col, elt['code'], string_format)
            sheet.write(i, col + 1, elt['name'], string_format)
            sheet.write(i, col + 2, elt['old_amount'], amount_format)
            sheet.write(i, col + 3, elt['new_amount'], amount_format)
            sheet.write(i, col + 4, elt['ecart'], amount_format)
            sheet.write(i, col + 5, '', string_format)
            i += 1

    def generate_xlsx_report(self, workbook, data, obj):
        codes = obj.getCodes()
        obj.getOldPeriodes()
        old_lines = obj.getpayslipLinesForPeriode(codes, obj.old_date_from, obj.old_date_to)

        new_lines = obj.getpayslipLinesForPeriode(codes, obj.date_from, obj.date_to)

        results = obj.getVariationByRule(codes)

        sheet = workbook.add_worksheet('RECAPITULATIF DES SALAIRES / REGLE SALARIALE')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.header_format)
        content_format = workbook.add_format(self.content_format)
        string_format = workbook.add_format(self.string_format)
        amount_format = workbook.add_format(self.amount_format)
        # self.formatSheet(sheet)
        i = 3
        self.generateHeaders(sheet, header_format)
        self.generateLines(sheet, results, string_format, content_format, amount_format)
        # workbook.close()
