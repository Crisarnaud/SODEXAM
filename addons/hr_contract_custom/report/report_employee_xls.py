import xlsxwriter
from odoo import models, fields
from datetime import datetime, timedelta


class EmployeeXlsx (models.AbstractModel):
    _name = 'report.hr_contract_custom.report_employee_xls'
    _inherit = 'report.report_xlsx.abstract'

    title = [
        "MTLE",
        "NOM & PRENOMS",
        "CATEGORIE",
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
        'identification_id','name', "cat", 'college', 'job_id', 'service_id', 'department_id',
        'direction_id',
        'gender', "start_date", 'birthday', 'age', 'type_contrat'
    ]
    # Formattage pour les headers
    header_format = {
        'bold': 1,
        'border': 1,
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': 'silver',
        'text_wrap': 1,
        'font_name': 'Helvetica'
    }

    content_format = {
        'bold': 0,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'fg_color': 'white',
        'num_format': '# ##0',
        'font_name': 'Helvetica'
    }

    amount_format = {
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'num_format': 'dd/mm/yy',
        'font_name': 'Helvetica'
    }

    amount_total_format = {
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '# ##0',
        'fg_color': 'gray',
        'font_name': 'Helvetica'
    }

    def formatSheet(self, sheet):
        sheet.add_table ('A1:M1', {'autofilter': True})
        sheet.set_default_row (30)
        sheet.set_row (0, 25)
        sheet.set_column ('A:A', 8)
        sheet.set_column ('B:B', 13)
        sheet.set_column ('C:C', 13)
        sheet.set_column ('D:D', 35)
        sheet.set_column ('E:E', 30)
        sheet.set_column ('F:F', 30)
        sheet.set_column ('G:G', 35)
        sheet.set_column ('H:H', 35)
        sheet.set_column ('I:I', 35)
        sheet.set_column ('J:J', 10)
        sheet.set_column ('K:K', 17)
        sheet.set_column ('L:L', 17)
        sheet.set_column ('M:M', 17)
    def generateLines(self, sheet,lines,content_format):
        u=1
        for line in lines:
            col = 0
            for i in range(len(self.cols)):
                key = self.cols[i]
                sheet.write(u, col, line[key], content_format)
                col += 1
            # sheet.write (i, 0, line['identification_id'] or '',content_format)
            # sheet.write (i, 1, line['name'] or '', content_format)
            # sheet.write (i, 2, line['cat'] or '', content_format)
            # sheet.write (i, 3, line['college'] or '', content_format)
            # sheet.write (i, 4, line['job_id'] or '',content_format)
            # sheet.write (i, 5, line['service_id'] or '', content_format)
            # sheet.write (i, 6, line['department_id'] or '', content_format)
            # sheet.write (i, 7, line['direction_id'] or '', content_format)
            # sheet.write (i, 8, line['gender'] or '', content_format)
            # sheet.write (i, 9, line['start_date'] or '', content_format)
            # sheet.write (i, 10, line['birthday'] or '', content_format)
            # sheet.write (i, 11, line['age'] or '', content_format)
            # sheet.write (i, 12, line['category_id'] or '',content_format)
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
        gender = data['gender']
        tab_name = 'LISTE DU PERSONNEL'
        if gender == 'male':
            tab_name = tab_name + ' ' + 'MASCULIN'
        if gender == 'female':
            tab_name = tab_name + ' ' + 'FEMININ'
        sheet = workbook.add_worksheet (tab_name)
        bold = workbook.add_format ({'bold': True})
        header_format = workbook.add_format (self.header_format)
        content_format = workbook.add_format (self.content_format)
        self.formatSheet (sheet)
        self.writeHeaders (sheet, obj,header_format)
        self.generateLines (sheet, lines,content_format)
        workbook.close()

