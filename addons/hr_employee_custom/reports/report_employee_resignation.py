from odoo import models, fields
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class PartnerXlsx(models.AbstractModel):
    _name = 'report.hr_employee_custom.report_employee_resignation'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Rapport des départs des employés"

    title = [
        "MATRICULE",
        "NOM & PRENOMS",
        "CATEGORIE SALARIALE",
        "CATEGORIE",
        "FONCTION",
        "SERVICE",
        "DEPARTEMENT",
        "DIRECTION",
        "SEXE",
        "EMBAUCHE",
        "NAISSANCE",
        "AGE",
        "NATURE DU CONTRAT",
        "DATE DE DEPART",
        "MOTIF DE DEPART",
    ]

    cols = [
        'matricule', 'name','cat', 'college', 'job_id', 'service_id', 'department_id', 'direction_id',
        'gender', 'date_embauche', 'birthday', 'age', 'type_contrat', 'date_depart',
        'motif_depart'
    ]


    # Formattage pour les headers
    h_format = {
        'bold': 1,
        'border': 1,
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': 'silver',
        'text_wrap': 0,
        'font_name': 'Helvetica'
    }

    c_format = {
        'bold': 0,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'fg_color': 'white',
        'text_wrap': 0,
        'num_format': 'dd/mm/yyyy',
        'font_name': 'Helvetica'
    }

    a_format = {
        'border': 1,
        'font_size': 10,
        'align': 'left',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Helvetica'
    }

    def formatSheet(self, sheet):
        sheet.add_table ('A1:O1', {'autofilter': True})
        sheet.set_default_row (30)
        sheet.set_row (0, 25)
        sheet.set_column ('A:A', 13)
        sheet.set_column ('B:B', 13)
        sheet.set_column ('C:C', 13)
        sheet.set_column ('D:D', 27)
        sheet.set_column ('E:E', 30)
        sheet.set_column ('F:F', 25)
        sheet.set_column ('G:G', 24)
        sheet.set_column ('H:H', 24)
        sheet.set_column ('I:I', 24)
        sheet.set_column ('J:J', 11)
        sheet.set_column ('K:K', 16)
        sheet.set_column ('L:L', 16)
        sheet.set_column ('M:M', 15)
        sheet.set_column ('N:N', 10)
        sheet.set_column ('O:O', 15)

    def generateLines(self, sheet, lines,content_format):
        u=1
        for line in lines:
            col = 0
            for i in range(len(self.cols)):
                key = self.cols[i]
                sheet.write(u, col, line[key], content_format)
                col += 1
            u += 1

    def writeHeaders(self, sheet, obj,header_format):
        line = 0
        col = 0
        for i in range (len (self.title)):
            sheet.write (line, col, self.title[i], header_format)
            col += 1
        line += 1

    def generate_xlsx_report(self, workbook, data, obj):
        lines = data['lines']
        sheet = workbook.add_worksheet ('LISTE DES DEPARTS PAR MOTIF')
        header_format = workbook.add_format (self.h_format)
        content_format = workbook.add_format (self.c_format)
        string_format = workbook.add_format (self.a_format)
        self.formatSheet (sheet)
        self.writeHeaders (sheet, obj, header_format)
        self.generateLines (sheet, lines, content_format)
        workbook.close ()