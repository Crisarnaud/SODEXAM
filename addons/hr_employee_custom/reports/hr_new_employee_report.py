import xlsxwriter

from odoo import models, fields
from datetime import datetime, timedelta


class PartnerXlsx(models.AbstractModel):
    _name = 'report.hr_employee_custom.report_new_employee'
    _inherit = 'report.report_xlsx.abstract'

    title = [
        "MTLE",
        "NOM & PRENOMS",
        "CATEGORIE SALARIALE",
        "CATEGORIE",
        "FONCTION",
        "SERVICES",
        "DEPARTEMENTS",
        "DIRECTION",
        "SEXE",
        "EMBAUCHE",
        "NAISSANCE",
        "AGE",
        "NATURE DU CONTRAT",
    ]

    cols = [
        'identification_id', 'name', "cat", 'college', 'job_id', 'service_id', 'department_id',
        'direction_id','gender', "start_date", 'birthday', 'age', 'type_contrat'
    ]


    # Formattage pour les headers
    h_format = {
        'bold': 1,
        'border': 1,
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': 'silver',
        'text_wrap': 1,
        'font_name': 'Helvetica'
    }

    c_format = {
        'bold': 0,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'fg_color': 'white',
        'num_format': '# ##0',
        'font_name': 'Helvetica'
    }

    a_format = {
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'num_format': 'dd/mm/yy',
        'font_name': 'Helvetica'
    }

    def formatSheet(self, sheet):
        sheet.add_table ('A1:M1', {'autofilter': True})
        sheet.set_default_row (30)
        sheet.set_row (0, 25)
        sheet.set_column ('A:A', 6)
        sheet.set_column ('B:B', 10)
        sheet.set_column ('C:C', 11)
        sheet.set_column ('D:D', 45)
        sheet.set_column ('E:E', 30)
        sheet.set_column ('F:F', 25)
        sheet.set_column ('G:G', 25)
        sheet.set_column ('H:H', 40)
        sheet.set_column ('I:I', 40)
        sheet.set_column ('J:J', 5)
        sheet.set_column ('K:K', 10)
        sheet.set_column ('L:L', 10)
        sheet.set_column ('M:M', 10)


    def generateLines(self, sheet, lines, content_format):
        u = 1
        for line in lines:
            col = 0
            for i in range (len (self.cols)):
                key = self.cols[i]
                sheet.write (u, col, line[key], content_format)
                col += 1
            u += 1

    def writeHeaders(self, sheet, obj, header_format=None):
        line = 0
        col = 0
        for i in range (len (self.title)):
            sheet.write (line, col, self.title[i], header_format)
            col += 1
        line += 1

    def generate_xlsx_report(self, workbook, data, obj):
        lines = data['lines']
        sheet = workbook.add_worksheet ('LISTE DES NOUVELLES RECRUES')
        header_format = workbook.add_format (self.h_format)
        content_format = workbook.add_format (self.c_format)
        amount_format = workbook.add_format (self.a_format)
        self.formatSheet (sheet)
        self.writeHeaders (sheet, obj, header_format)
        self.generateLines (sheet, lines, content_format)
        workbook.close ()

