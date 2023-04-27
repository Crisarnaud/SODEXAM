# -*- coding:utf-8 -*-

import datetime

from odoo import models


class HrPayrollPayrollWizardXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_custom.hr_301_list_report_recap_xls'
    _inherit = 'report.report_xlsx.abstract'

    title = []
    h_format = {
        'bold': 1,
        'border': 1,
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#cccccc',
        'text_wrap': 1
    }

    c_format = {
        'bold': 0,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'white'
    }

    l_format = {
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
        'num_format': '### ### ### ##0'
    }

    a_total_format = {
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '### ### ##0',
        'fg_color': 'gray',
    }

    def formatSheet(self, sheet):
        sheet.set_column('A:A', 11)
        sheet.set_column('B:B', 11)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 30)
        sheet.set_column('H:H', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('L:L', 30)
        sheet.set_column('N:N', 30)
        sheet.set_column('E:ZZ', 15)

    def generateLines(self, sheet, obj, header_format, content_format, left_format, amount_format, amount_total_format):
        total_amount_brut_total = []
        total_natural_advantage_software = []
        total_natural_advantage_other = []
        total_cash_advantage = []
        total_total_gross = []
        total_amount_is = []
        total_amount_cn = []
        total_amount_igr = []
        total_amount_tp_af = []
        a = 0
        i = 0

        sheet.merge_range(0, 0, 1, 0, 'Matricule', header_format)
        sheet.merge_range(0, 1, 1, 1, 'Ordre', header_format)
        sheet.merge_range(0, 2, 1, 2, 'Noms et Prenoms', header_format)
        sheet.merge_range(0, 3, 1, 3, 'Emploi ou qualité', header_format)
        sheet.merge_range(0, 4, 1, 4, 'Code emploi', header_format)
        sheet.merge_range(0, 5, 1, 5, 'Reg(Nor.Agr)', header_format)
        sheet.merge_range(0, 6, 1, 6, 'Sexe', header_format)
        sheet.merge_range(0, 7, 1, 7, 'Nationalité', header_format)
        sheet.merge_range(0, 8, 1, 8, 'Local ou expatrié', header_format)
        sheet.merge_range(0, 9, 0, 11, "Sit.Fam.La+Fav", header_format)
        sheet.write(1, 9, 'Cel.Mar.Div', header_format)
        sheet.write(1, 10, "Nbre d'enfts", header_format)
        sheet.write(1, 11, "Parts IGR", header_format)
        sheet.merge_range(0, 12, 1, 12, 'Nbre de jours actualisé', header_format)
        sheet.merge_range(0, 13, 1, 13, 'Montant des salaires logiciel', header_format)
        sheet.merge_range(0, 14, 1, 14, 'Avantage en nature logiciel', header_format)
        sheet.merge_range(0, 15, 1, 15, 'Avantage en nature autre', header_format)
        sheet.merge_range(0, 16, 1, 16, 'Avantage en espèce', header_format)
        sheet.write(0, 17, 'Salaires bruts', header_format)
        sheet.write(1, 17, 'Tous personnel', header_format)
        sheet.merge_range(0, 18, 1, 18, 'IS', header_format)
        sheet.merge_range(0, 19, 1, 19, 'CN', header_format)
        sheet.merge_range(0, 20, 1, 20, 'IGR', header_format)
        sheet.merge_range(0, 21, 0, 22, 'Indemnités exonérées', header_format)
        sheet.write(1, 21, 'Montant logiciel(TP+ALLOC.FAM)', header_format)
        sheet.write(1, 22, 'Désignation', header_format)
        j = 2
        for line in obj.line_ids:
            total_amount_brut_total.append(line.amount_brut_total)
            total_natural_advantage_software.append(line.natural_advantage_software)
            total_natural_advantage_other.append(line.natural_advantage_other)
            total_cash_advantage.append(line.cash_advantage)
            total_total_gross.append(line.total_gross)
            total_amount_is.append(line.amount_is)
            total_amount_cn.append(line.amount_cn)
            total_amount_igr.append(line.amount_igr)
            total_amount_tp_af.append(line.amount_tp)
            total_amount_tp_af.append(line.amount_af)
            i += 1
            if line.employee_id:
                if len(line.employee_id.identification_id) < 6:
                    sheet.write(j, 0, str(0) + line.employee_id.identification_id, content_format)
                sheet.write(j, 1, a + i, content_format)
                sheet.write(j, 2, line.employee_id.name + ' ' + line.employee_id.first_name, left_format)
                sheet.write(j, 3, line.employee_id.job_id.name if line.employee_id.job_id else '', left_format)
                sheet.write(j, 4, '', content_format)
                sheet.write(j, 5, 'N', content_format)
                sheet.write(j, 6, line.employee_id.gender[0].capitalize() if line.employee_id.gender else '', content_format)
                sheet.write(j, 7, line.employee_id.country_id.code if line.employee_id.country_id else '',
                            content_format)
                sheet.write(j, 8, line.nature_employee[0].capitalize(), content_format)
                sheet.write(j, 9, line.employee_id.marital[0].capitalize(), content_format)
                sheet.write(j, 10, line.employee_id.child_in_charge, content_format)
                sheet.write(j, 11, line.employee_id.part_igr, content_format)
                sheet.write(j, 12, line.total_worked_days, content_format)
                sheet.write(j, 13, line.amount_brut_total, amount_format)
                sheet.write(j, 14, line.natural_advantage_software, amount_format)
                sheet.write(j, 15, line.natural_advantage_other, amount_format)
                sheet.write(j, 16, line.cash_advantage, amount_format)
                sheet.write(j, 17, line.total_gross, amount_format)
                sheet.write(j, 18, line.amount_is, amount_format)
                sheet.write(j, 19, line.amount_cn, amount_format)
                sheet.write(j, 20, line.amount_igr, amount_format)
                sheet.write(j, 21, line.amount_af + line.amount_tp, amount_format)
                sheet.write(j, 22, line.employee_id.motif_fin_contract_id.name
                if line.employee_id.motif_fin_contract_id and line.employee_id.end_date else '', content_format)
                j += 1
        sheet.merge_range(j, 0, j, 12, 'Total', content_format)
        sheet.write(j, 13, sum(total_amount_brut_total), amount_format)
        sheet.write(j, 14, sum(total_natural_advantage_software), amount_format)
        sheet.write(j, 15, sum(total_natural_advantage_other), amount_format)
        sheet.write(j, 16, sum(total_cash_advantage), amount_format)
        sheet.write(j, 17, sum(total_total_gross), amount_format)
        sheet.write(j, 18, sum(total_amount_is), amount_format)
        sheet.write(j, 19, sum(total_amount_cn), amount_format)
        sheet.write(j, 20, sum(total_amount_igr), amount_format)
        sheet.write(j, 21, sum(total_amount_tp_af), amount_format)
        sheet.write(j, 22, '', amount_format)

    def writeHeaders(self, sheet, obj, header_format):
        col = 0
        line = 0
        sheet.set_default_row(30)
        for i in range(len(self.title)):
            sheet.write(line, col, self.title[i], header_format)
            col += 1
        line += 1

    def generate_xlsx_report(self, workbook, data, obj):
        sheet = workbook.add_worksheet('ETAT RECAPITULATIF DES SALAIRES')
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(self.h_format)
        content_format = workbook.add_format(self.c_format)
        left_format = workbook.add_format(self.l_format)
        amount_format = workbook.add_format(self.a_format)
        amount_total_format = workbook.add_format(self.a_total_format)
        self.formatSheet(sheet)
        self.writeHeaders(sheet, obj, header_format)
        self.generateLines(sheet, obj, header_format, content_format, left_format, amount_format, amount_total_format)
