# -*- coding:utf-8 -*-

import datetime
from odoo import models, api, _


class HrCRRAEapportXlsx(models.AbstractModel):
    _name = "report.hr_payroll_custom.hr_crrae_raport_xlsx"
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
        'fg_color': 'white'
    }

    amount_format = {
        'bold': 0,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '### ### ##0'
    }

    headers = (
        "REGIME DE RETRAITE(O)",
        "MATRICULE ENTREPRISE(O)",
        "MATRICULE CRRAE(O)",
        "NOM(O)",
        "PRENOMS(O)",
        "TYPE COTISATION(O)",
        "PERIODE DE COTISATION",
        "PERIODE A REGULARISER (F)",
        "ASSIETTE",
        "MOTIF CHANGEMENT ASSIETTE(F)",
        "PART EMPLOYE(O)",
        "PART EMPLOYEUR(O)",
        "TOTAL COTISATION(O)",
        "TOTAL(O)",
        "ETAT PARTICIPANT(F)",
        "DATE DE CHANGEMENT D'ÉTAT(F)",
        "PART EMPLOYÉ FAAM",
        "PART EMPLOYEUR FAAM",
        "TOTAL COTISATION FAAM"
    )

    def formatSheet(self, sheet):
        sheet.set_row(0, 50)
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:D', 25)
        sheet.set_column('E:E', 50)
        sheet.set_column('F:S', 15)

    def generateHeaders(self, sheet, header_format):
        i = 0
        col = 0
        sheet.write_row(i, col, self.headers, header_format)
        i += 1

    def generateLine(self, sheet, obj, content_format, amount_format):
        # if dt['crrae_employer']:
        i = 0
        line = i
        for rec in obj.payroll_crrae_line_ids:
            sheet.write(line, 0, 'RRPC', content_format)
            sheet.write(line, 1, rec.employee_id.identification_id or '', content_format)
            sheet.write(line, 2, rec.employee_id.num_crrae or '', content_format)
            sheet.write(line, 3, rec.employee_id.name or '', content_format)
            sheet.write(line, 4, rec.employee_id.first_name or '', content_format)
            sheet.write(line, 5, "NOR", content_format)
            sheet.write(line, 6, obj.periode or '', content_format)
            sheet.write(line, 7, obj.periode_regul or '', content_format)
            sheet.write(line, 8, obj.assiette or '', content_format)
            sheet.write(line, 9, obj.motif_changement or '', content_format)
            sheet.write(line, 10, rec.crrae_employee or '', amount_format)
            sheet.write(line, 11, rec.crrae_employer or '', amount_format)
            sheet.write(line, 12, (rec.crrae_employee + rec.crrae_employer) or '', amount_format)
            sheet.write(line, 13, (rec.crrae_employee + rec.crrae_employer) or '', amount_format)
            sheet.write(line, 14, '', content_format)
            sheet.write(line, 15, '', content_format)
            sheet.write(line, 16, rec.faam_employee or '', amount_format)
            sheet.write(line, 17, rec.faam_employer or '', amount_format)
            sheet.write(line, 18, (rec.faam_employee + rec.faam_employer) or '', amount_format)
            line += 1
        i = line

    def generateLinesTotaux(self, sheet, totaux, codes, amount_format, content_format):
        col = 0
        i = 0
        sheet.write(i, col, 'TOTAUX', content_format)
        for code in codes:
            col += 1
            sheet.write(i, col, totaux[code], amount_format)
        i += 1

    def generate_xlsx_report(self, workbook, data, obj):
        sheet = workbook.add_worksheet('CRRAE')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.header_format)
        content_format = workbook.add_format(self.content_format)
        amount_format = workbook.add_format(self.amount_format)
        self.formatSheet(sheet)
        i = 0
        self.generateHeaders(sheet, header_format)
        self.generateLine(sheet, obj, content_format, amount_format)
        workbook.close()
