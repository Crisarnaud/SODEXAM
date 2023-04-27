from dateutil.relativedelta import relativedelta

from odoo import models, fields
from datetime import datetime, timedelta, date
import calendar
import xlsxwriter


class HolidayMonthly(models.AbstractModel):
    _name = 'report.hr_holiday_custom.report_synthetic_holiday'
    _description = "Report synthetic holiday"
    _inherit = 'report.report_xlsx.abstract'

    now = datetime.now()

    title = [
        "MTLE",
        "NOM & PRENOMS",
        "SEXE",
        "FONCTION",
        "DÉPARTEMENT",
        "DIRECTION",
        "TOTAL Antérieur " + str((date.today() - relativedelta(years=1)).strftime('%Y')),
        "CONGÉS PREV " + str(now.year),
        "TOTAL " + str(now.year),
        "janv.-" + str(now.year),
        "févr.-" + str(now.year),
        'mars.-' + str(now.year),
        'avr.-' + str(now.year),
        "mai-" + str(now.year),
        "juin-" + str(now.year),
        "juil.-" + str(now.year),
        "août-" + str(now.year),
        "sept.-" + str(now.year),
        "oct.-" + str(now.year),
        "nov.-" + str(now.year),
        "déc.-" + str(now.year),
        "TOTAL JOURS de CONGÉS PRIS " + str(now.year),
        "STOCKS CONGÉS au 31 Déc." + str(now.year),
    ]
    cols = [
        'identification_id', 'name', 'gender', 'job_id', 'number_days_estimed_holidays', 'date_from', 'duree',
    ]

    months = [
        "janv.-" + str(now.year),
        "févr.-" + str(now.year),
        'mars-' + str(now.year),
        'avril-' + str(now.year),
        "mai-" + str(now.year),
        "juin-" + str(now.year),
        "juil.-" + str(now.year),
        "août-" + str(now.year),
        "sept.-" + str(now.year),
        "oct.-" + str(now.year),
        "nov.-" + str(now.year),
        "déc.-" + str(now.year),
    ]

    i = 0

    # Formattage pour les headerss
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
        sheet.add_table('A1:W1', {'autofilter': True})
        sheet.set_default_row(30)
        sheet.set_row(0, 35)
        sheet.set_column('A:A', 8)
        sheet.set_column('B:B', 35)
        sheet.set_column('C:C', 11)
        sheet.set_column('D:D', 35)
        sheet.set_column('E:E', 35)
        sheet.set_column('F:F', 35)
        sheet.set_column('G:G', 17)
        sheet.set_column('H:H', 10)
        sheet.set_column('I:I', 10)
        sheet.set_column('J:J', 10)
        sheet.set_column('K:K', 10)
        sheet.set_column('L:L', 10)
        sheet.set_column('M:M', 10)
        sheet.set_column('N:N', 10)
        sheet.set_column('O:O', 10)
        sheet.set_column('P:P', 10)
        sheet.set_column('Q:Q', 10)
        sheet.set_column('R:R', 10)
        sheet.set_column('S:S', 10)
        sheet.set_column('T:T', 10)
        sheet.set_column('U:U', 10)
        sheet.set_column('V:V', 15)
        sheet.set_column('W:W', 15)

    def generateLines(self, sheet, lines, content_format):
        leaves = self.env['hr.leave']
        row = 1
        for line in lines:
            duree = []
            sheet.write(row, 0, line['identification_id'] or '', content_format)
            sheet.write(row, 1, line['name'] or '', content_format)
            sheet.write(row, 2, line['gender'] or '', content_format)
            sheet.write(row, 3, line['job_id'] or '', content_format)
            sheet.write(row, 4, line['department_id'] or '', content_format)
            sheet.write(row, 5, line['direction_id'] or '', content_format)
            sheet.write(row, 6, line['stock_holiday'] or '', content_format)
            sheet.write(row, 7, line['number_days_estimed_holidays'] or '', content_format)
            sheet.write(row, 8, line['total'] or '', content_format)
            sheet.write(row, 9, '', content_format)
            sheet.write(row, 10, '', content_format)
            sheet.write(row, 11, '', content_format)
            sheet.write(row, 12, '', content_format)
            sheet.write(row, 13, '', content_format)
            sheet.write(row, 14, '', content_format)
            sheet.write(row, 15, '', content_format)
            sheet.write(row, 16, '', content_format)
            sheet.write(row, 17, '', content_format)
            sheet.write(row, 18, '', content_format)
            sheet.write(row, 19, '', content_format)
            sheet.write(row, 20, '', content_format)
            leaves_emp = leaves.search([('state', '=', 'validate'), ('holiday_status_id.code', '=', 'CONG')])
            o = 7
            for i in self.months:
                o += 1
                for leave in leaves_emp:
                    if leave.employee_id.identification_id == line['identification_id'] and i == leave.request_date_from.strftime('%b-%Y'):
                        sheet.write(row, o, leave.number_of_days_display or '', content_format)
                        duree.append(leave.number_of_days_display)
            sheet.write(row, 21, sum(duree) or 0, content_format)
            sheet.write(row, 22, line['total'] - sum(duree) or 0, content_format)
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
        sheet = workbook.add_worksheet('RAPPORT SYNTHÉTIQUE DES CONGÉS')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.h_format)
        content_format = workbook.add_format(self.c_format)
        amount_format = workbook.add_format(self.a_format)
        amount_total_format = workbook.add_format(self.a_total_format)
        self.formatSheet(sheet)
        line = 0
        col = 0
        self.writeHeaders(sheet, obj, header_format)
        self.generateLines(sheet, lines, content_format)
