import xlsxwriter

from odoo import models, fields
from datetime import datetime, timedelta


class PartnerXlsx(models.AbstractModel):
    _name = 'report.hr_holiday_custom.report_all_holidays_department'
    _description = "Report all holidays for department"
    _inherit = 'report.report_xlsx.abstract'

    title = [
        "MTLE",
        "NOM & PRENOMS",
        "SEXE",
        "FONCTION",
        "SERVICE",
        "DEPARTEMENT",
        "DIRECTION",
        "TYPE CONGÉ",
        "DATE DE DEBUT",
        "DATE DE FIN",
        "NBRE DE JRS CONGES",
]

    cols = [
        'identification_id', 'name', 'gender', 'job_id', 'service_id', 'department_id', 'direction_id',
         'holiday_status_id', 'date_start', 'date_return', 'duree'
    ]

    i = 0

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

    a_total_format = {
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '# ##0',
        'fg_color': 'gray',
        'font_name': 'Helvetica'
    }

    def formatSheet(self, sheet):
        sheet.add_table('A1:J1', {'autofilter': True})
        sheet.set_default_row(30)
        sheet.set_row(0, 35)
        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 11)
        sheet.set_column('D:D', 35)
        sheet.set_column('E:E', 40)
        sheet.set_column('F:F', 35)
        sheet.set_column('G:G', 35)
        sheet.set_column('H:H', 35)
        sheet.set_column('I:I', 19)
        sheet.set_column('J:J', 10)

    def generateLines(self, sheet, lines, content_format):
        row = 1
        for line in lines:
            col = 0
            for i in range(len(self.cols)):
                key = self.cols[i]
                sheet.write(row, col, line[key] or '', content_format)
                col += 1
            row += 1

    def writeHeaders(self, sheet, obj, header_format):
        col = 0
        line = 0
        for i in range(len(self.title)):
            sheet.write(line, col, self.title[i], header_format)
            col += 1
        line += 1

    def generate_xlsx_report(self, workbook, data, obj):
        lines = data['lines']
        sheet = workbook.add_worksheet('RAPPORT DES CONGÉS')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.h_format)
        content_format = workbook.add_format(self.c_format)
        amount_format = workbook.add_format(self.a_format)
        amount_total_format = workbook.add_format(self.a_total_format)
        self.formatSheet(sheet)
        line = 0
        self.writeHeaders(sheet, obj, header_format)
        self.generateLines(sheet, lines, content_format)

