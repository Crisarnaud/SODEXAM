# -*- coding:utf-8 -*-

import datetime

from odoo import models


class HrDISA(models.AbstractModel):
    _name = 'report.hr_payroll_custom.report_hr_disa'
    _inherit = 'report.report_xlsx.abstract'

    title = [
        "N°ORDRE",
        "NOM",
        "PRENOMS",
        "N° C.N.P.S",
        "ANNEE DE NAISSANCE",
        "DATE D’EMBAUCHE",
        "DATE DE DEPART",
        "SALAIRE HORAIRES OU MENSUELS",
        "SALAIRE BRUT NON PLAFONNE",
        "NOMBRE DE MOIS TRAVAILLE",
        "SALAIRE ANNUEL SOULIS A COTISATION AT/PF",
        "SALAIRE ANNUEL SOUMIS A COTISATION AU TITRE DU REGIME RETRAITE",
        "LE SALARIE COTISE AU TITRE:\n 1=AM \n 2=PF \n 3=AT \n 4=RETRAITE",
        "OBS"
    ]

    # cols = [
    #     'order', 'employee_name', 'num_cnps', 'date_naissance', 'date_embauche', 'date_depart', 'type_employee',
    #     'temps_travail', 'brut_total', 'brut_autre', 'brut_cnps', 'cotisation', 'comment'
    # ]

    i = 0

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
        'align': 'left',
        'valign': 'vcenter',
        'fg_color': 'white'
    }

    a_format = {
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '### ### ##0'
    }

    a_total_format = {
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '# ##0',
        'fg_color': 'gray',
    }

    def formatSheet(self, sheet):
        sheet.set_row(0, 80)
        sheet.set_column('A:A', 7)
        sheet.set_column('B:B', 22)
        sheet.set_column('C:C', 33)
        sheet.set_column('D:G', 15)
        sheet.set_column('H:H', 12)
        sheet.set_column('I:I', 20)
        sheet.set_column('J:J', 10)
        sheet.set_column('K:L', 20)
        sheet.set_column('M:M', 13)
        sheet.set_column('N:N', 20)

    def generateLines(self, sheet, obj, content_format, amount_format):
        i = 1
        for line in obj.disa_line_ids:
            col = 0
            sheet.write(i, col, line.employee_id.identification_id, content_format)
            sheet.write(i, col + 1, line.employee_id.name, content_format)
            sheet.write(i, col + 2, line.employee_id.first_name, content_format)
            sheet.write(i, col + 3, line.num_cnps, content_format)
            sheet.write(i, col + 4, line.birthday, content_format)
            sheet.write(i, col + 5, line.hiring_date, content_format)
            sheet.write(i, col + 6, line.date_of_departure, content_format)
            sheet.write(i, col + 7, line.employee_type, content_format)
            sheet.write(i, col + 8, line.total_gross + line.natural_advantage, amount_format)
            sheet.write(i, col + 9, line.work_time, amount_format)
            sheet.write(i, col + 10, line.other_gross, amount_format)
            sheet.write(i, col + 11, line.cnps_gross, amount_format)
            sheet.write(i, col + 12, line.contribution, content_format)
            sheet.write(i, col + 13, line.comment, content_format)
            i += 1

    def writeHeaders(self, sheet, obj, header_format):
        col = 0
        line = 0
        sheet.write_row(line, col, self.title, header_format)
        line += 1

    def generate_xlsx_report(self, workbook, data, obj):
        sheet = workbook.add_worksheet('DISA')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.h_format)
        content_format = workbook.add_format(self.c_format)
        amount_format = workbook.add_format(self.a_format)
        self.formatSheet(sheet)
        line = 0
        self.writeHeaders(sheet, obj, header_format)
        self.generateLines(sheet, obj, content_format, amount_format)
        workbook.close()
