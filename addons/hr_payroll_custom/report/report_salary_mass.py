# -*- coding:utf-8 -*-

import datetime
import logging
from odoo import models, api, _

_logger = logging.getLogger(__name__)

class HrPayrollSalaryMass(models.AbstractModel):
    _name = 'report.hr_payroll_custom.salary_mass_xls'
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
        'align': 'center',
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
        'align': 'center',
        'valign': 'vcenter',
        'color': 'black',
        'fg_color': 'white',
        'num_format': '### ### ##0'
    }

    def formatSheet(self, sheet):
        sheet.set_default_row(16)
        sheet.set_column('A:A', 17)
        sheet.set_column('B:Z', 15)

    def generate_header(self, sheet, titre, header, tax_contribution_format):
        i = 0
        line = i
        sheet.merge_range(line, 0, line, 2, titre, tax_contribution_format)
        col = 1
        line += 2
        for elt in header:
            sheet.merge_range(line, col, line, col + 1, elt, tax_contribution_format)
            sheet.write(line + 1, col, 'F', tax_contribution_format)
            sheet.write(line + 1, col + 1, 'H', tax_contribution_format)
            col += 2
        sheet.merge_range(line, col, line, col + 1, 'Total', tax_contribution_format)
        sheet.write(line + 1, col, 'F', tax_contribution_format)
        sheet.write(line + 1, col + 1, 'H', tax_contribution_format)
        sheet.merge_range(line, col + 2, line + 1, col + 2, 'Total', tax_contribution_format)
        line += 2
        i = line

    def generate_salary_mass_header(self, sheet, titre, header, tax_contribution_format):
        i = 30
        line = i
        sheet.merge_range(line, 0, line, 2, titre, tax_contribution_format)
        col = 1
        line += 2
        for elt in header:
            sheet.merge_range(line, col, line, col + 1, elt, tax_contribution_format)
            sheet.write(line + 1, col, 'F', tax_contribution_format)
            sheet.write(line + 1, col + 1, 'H', tax_contribution_format)
            col += 2
        sheet.merge_range(line, col, line, col + 1, 'Total', tax_contribution_format)
        sheet.write(line + 1, col, 'F', tax_contribution_format)
        sheet.write(line + 1, col + 1, 'H', tax_contribution_format)
        sheet.merge_range(line, col + 2, line + 1, col + 2, 'Total', tax_contribution_format)
        line += 2
        i = line

    def generate_lines(self, sheet, country_header, country_lines, content_label_format, content_number_format,
                       cumul_label_format, cumul_number_format):
        i = 4
        line = i
        list_country = {}
        for country in country_header:
            list_country[country + 'female'] = 0
            list_country[country + 'male'] = 0
        cumul_row_female = 0
        cumul_row_male = 0
        for rec in country_lines:
            sheet.write(line, 0, rec['category'] or '', content_label_format)
            col = 1
            total_row_female = 0
            total_row_male = 0
            for country_data in rec['data_nationality']:
                for gender in country_data['gender']:
                    sheet.write(line, col, gender['female'] if gender['female'] else '', content_number_format)
                    sheet.write(line, col + 1, gender['male'] if gender['male'] else '', content_number_format)
                    total_row_female += gender['female']
                    total_row_male += gender['male']
                    list_country[country_data['country'] + 'female'] += gender['female']
                    list_country[country_data['country'] + 'male'] += gender['male']
                col += 2
            cumul_row_female += total_row_female
            cumul_row_male += total_row_male
            sheet.write(line, col, total_row_female, cumul_number_format)
            sheet.write(line, col + 1, total_row_male, cumul_number_format)
            sheet.write(line, col + 2, total_row_female + total_row_male, cumul_number_format)
            line += 1

        sheet.write(line, 0, 'Sous total', cumul_label_format)
        col = 1
        for country in country_header:
            sheet.write(line, col, list_country[country + 'female'], cumul_number_format)
            sheet.write(line, col + 1, list_country[country + 'male'], cumul_number_format)
            col += 2
        sheet.write(line, col, cumul_row_female, cumul_number_format)
        sheet.write(line, col + 1, cumul_row_male, cumul_number_format)
        sheet.write(line, col + 2, cumul_row_female + cumul_row_male, cumul_number_format)

        line += 1
        sheet.write(line, 0, 'Total', cumul_label_format)
        col = 1
        for country in country_header:
            sheet.merge_range(line, col, line, col + 1,
                              list_country[country + 'female'] + list_country[country + 'male'], cumul_number_format)
            col += 2
        sheet.merge_range(line, col, line, col + 1, cumul_row_female + cumul_row_male, cumul_number_format)

        i = line + 3

    def generate_salary_mass_lines(self, sheet, country_header, country_lines, content_label_format, content_number_format,
                       cumul_label_format, cumul_number_format):
        i = 36
        line = i
        list_country = {}
        for country in country_header:
            list_country[country + 'female'] = 0
            list_country[country + 'male'] = 0
        cumul_row_female = 0
        cumul_row_male = 0
        for rec in country_lines:
            sheet.write(line, 0, rec['category'] or '', content_label_format)
            col = 1
            total_row_female = 0
            total_row_male = 0
            for country_data in rec['data_nationality']:
                for gender in country_data['gender']:
                    sheet.write(line, col, gender['female'] if gender['female'] else '', content_number_format)
                    sheet.write(line, col + 1, gender['male'] if gender['male'] else '', content_number_format)
                    total_row_female += gender['female']
                    total_row_male += gender['male']
                    list_country[country_data['country'] + 'female'] += gender['female']
                    list_country[country_data['country'] + 'male'] += gender['male']
                col += 2
            cumul_row_female += total_row_female
            cumul_row_male += total_row_male
            sheet.write(line, col, total_row_female, cumul_number_format)
            sheet.write(line, col + 1, total_row_male, cumul_number_format)
            sheet.write(line, col + 2, total_row_female + total_row_male, cumul_number_format)
            line += 1

        sheet.write(line, 0, 'Sous total', cumul_label_format)
        col = 1
        for country in country_header:
            sheet.write(line, col, list_country[country + 'female'], cumul_number_format)
            sheet.write(line, col + 1, list_country[country + 'male'], cumul_number_format)
            col += 2
        sheet.write(line, col, cumul_row_female, cumul_number_format)
        sheet.write(line, col + 1, cumul_row_male, cumul_number_format)
        sheet.write(line, col + 2, cumul_row_female + cumul_row_male, cumul_number_format)

        line += 1
        sheet.write(line, 0, 'Total', cumul_label_format)
        col = 1
        for country in country_header:
            sheet.merge_range(line, col, line, col + 1,
                              list_country[country + 'female'] + list_country[country + 'male'], cumul_number_format)
            col += 2
        sheet.merge_range(line, col, line, col + 1, cumul_row_female + cumul_row_male, cumul_number_format)

        i = line + 3

    def generate_salary_mass_total_brut_lines(self, sheet, year_header, year_lines, content_label_format, content_number_format,
                            cumul_label_format, cumul_number_format):
        i = 33
        line = i
        list_country = {}
        for year in year_header:
            list_country[year + 'female'] = 0
            list_country[year + 'male'] = 0
        cumul_row_female = 0
        cumul_row_male = 0
        for rec in year_lines:
            sheet.write(line, 0, rec['category'] or '', content_label_format)
            col = 1
            total_row_female = 0
            total_row_male = 0
            for year_data in rec['data_year']:
                for gender in year_data['gender']:
                    sheet.write(line, col, gender['female'] if gender['female'] else '', content_number_format)
                    sheet.write(line, col + 1, gender['male'] if gender['male'] else '', content_number_format)
                    sheet.write(line, col + 2, gender['female'] + gender['male'], cumul_number_format)
                    total_row_female += gender['female']
                    total_row_male += gender['male']
                    list_country[year_data['year'] + 'female'] += gender['female']
                    list_country[year_data['year'] + 'male'] += gender['male']
                col += 3
            cumul_row_female += total_row_female
            cumul_row_male += total_row_male
            line += 1
        sheet.write(line, 0, 'Total', cumul_label_format)
        col = 1
        for year in year_header:
            sheet.write(line, col, list_country[str(year) + 'female'], cumul_number_format)
            sheet.write(line, col + 1, list_country[str(year) + 'male'], cumul_number_format)
            sheet.write(line, col + 2, list_country[str(year) + 'female'] + list_country[str(year) + 'male'],
                        cumul_number_format)
            col += 3
        i = line + 3

    def generate_year_header(self, sheet, titre, header, tax_contribution_format):
        i = 15
        line = i
        sheet.merge_range(line, 0, line, 2, titre, tax_contribution_format)
        col = 1
        line += 2
        for elt in header:
            sheet.merge_range(line, col, line, col + 2, elt, tax_contribution_format)
            sheet.write(line + 1, col, 'F', tax_contribution_format)
            sheet.write(line + 1, col + 1, 'H', tax_contribution_format)
            sheet.write(line + 1, col + 2, 'Total', tax_contribution_format)
            col += 3
        line += 2
        i = line

    def generate_year_global_brut_header(self, sheet, titre, header, tax_contribution_format):
            i = 44
            line = i
            sheet.merge_range(line, 0, line, 2, titre, tax_contribution_format)
            col = 1
            line += 2
            for elt in header:
                sheet.merge_range(line, col, line, col + 2, elt, tax_contribution_format)
                sheet.write(line + 1, col, 'F', tax_contribution_format)
                sheet.write(line + 1, col + 1, 'H', tax_contribution_format)
                sheet.write(line + 1, col + 2, 'Total', tax_contribution_format)
                col += 3
            line += 2
            i = line

    def generate_year_header_brut_total(self, sheet, titre, header, tax_contribution_format):
            i = 29
            line = i
            sheet.merge_range(line, 0, line, 2, titre, tax_contribution_format)
            col = 1
            line += 2
            for elt in header:
                sheet.merge_range(line, col, line, col + 2, elt, tax_contribution_format)
                sheet.write(line + 1, col, 'F', tax_contribution_format)
                sheet.write(line + 1, col + 1, 'H', tax_contribution_format)
                sheet.write(line + 1, col + 2, 'Total', tax_contribution_format)
                col += 3
            line += 2
            i = line

    def generate_year_lines(self, sheet, year_header, year_lines, content_label_format, content_number_format,
                            cumul_label_format, cumul_number_format):
        i = 19
        line = i
        list_country = {}
        for year in year_header:
            list_country[year + 'female'] = 0
            list_country[year + 'male'] = 0
        cumul_row_female = 0
        cumul_row_male = 0
        for rec in year_lines:
            sheet.write(line, 0, rec['category'] or '', content_label_format)
            col = 1
            total_row_female = 0
            total_row_male = 0
            for year_data in rec['data_year']:
                for gender in year_data['gender']:
                    sheet.write(line, col, gender['female'] if gender['female'] else '', content_number_format)
                    sheet.write(line, col + 1, gender['male'] if gender['male'] else '', content_number_format)
                    sheet.write(line, col + 2, gender['female'] + gender['male'], cumul_number_format)
                    total_row_female += gender['female']
                    total_row_male += gender['male']
                    list_country[year_data['year'] + 'female'] += gender['female']
                    list_country[year_data['year'] + 'male'] += gender['male']
                col += 3
            cumul_row_female += total_row_female
            cumul_row_male += total_row_male
            line += 1
        sheet.write(line, 0, 'Total', cumul_label_format)
        col = 1
        for year in year_header:
            sheet.write(line, col, list_country[str(year) + 'female'], cumul_number_format)
            sheet.write(line, col + 1, list_country[str(year) + 'male'], cumul_number_format)
            sheet.write(line, col + 2, list_country[str(year) + 'female'] + list_country[str(year) + 'male'],
                        cumul_number_format)
            col += 3
        i = line + 3

    def generate_year_global_brut_lines(self, sheet, year_header, year_lines, content_label_format, content_number_format,
                            cumul_label_format, cumul_number_format):
        i = 48
        line = i
        list_country = {}
        for year in year_header:
            list_country[year + 'female'] = 0
            list_country[year + 'male'] = 0
        cumul_row_female = 0
        cumul_row_male = 0
        for rec in year_lines:
            sheet.write(line, 0, rec['category'] or '', content_label_format)
            col = 1
            total_row_female = 0
            total_row_male = 0
            for year_data in rec['data_year']:
                for gender in year_data['gender']:
                    sheet.write(line, col, gender['female'] if gender['female'] else '', content_number_format)
                    sheet.write(line, col + 1, gender['male'] if gender['male'] else '', content_number_format)
                    sheet.write(line, col + 2, gender['female'] + gender['male'], cumul_number_format)
                    total_row_female += gender['female']
                    total_row_male += gender['male']
                    list_country[year_data['year'] + 'female'] += gender['female']
                    list_country[year_data['year'] + 'male'] += gender['male']
                col += 3
            cumul_row_female += total_row_female
            cumul_row_male += total_row_male
            line += 1
        sheet.write(line, 0, 'Total', cumul_label_format)
        col = 1
        for year in year_header:
            sheet.write(line, col, list_country[str(year) + 'female'], cumul_number_format)
            sheet.write(line, col + 1, list_country[str(year) + 'male'], cumul_number_format)
            sheet.write(line, col + 2, list_country[str(year) + 'female'] + list_country[str(year) + 'male'],
                        cumul_number_format)
            col += 3
        i = line + 3

    def generate_year_lines_brut(self, sheet, year_header, year_lines, content_label_format, content_number_format,
                                cumul_label_format, cumul_number_format):
        i = 19
        line = i
        list_country = {}
        for year in year_header:
            list_country[year + 'female'] = 0
            list_country[year + 'male'] = 0
        cumul_row_female = 0
        cumul_row_male = 0
        for rec in year_lines:
            sheet.write(line, 0, rec['category'] or '', content_label_format)
            col = 1
            total_row_female = 0
            total_row_male = 0
            for year_data in rec['data_year']:
                for gender in year_data['gender']:
                    sheet.write(line, col, gender['female'] if gender['female'] else '', content_number_format)
                    sheet.write(line, col + 1, gender['male'] if gender['male'] else '', content_number_format)
                    sheet.write(line, col + 2, gender['female'] + gender['male'], cumul_number_format)
                    total_row_female += gender['female']
                    total_row_male += gender['male']
                    list_country[year_data['year'] + 'female'] += gender['female']
                    list_country[year_data['year'] + 'male'] += gender['male']
                col += 3
            cumul_row_female += total_row_female
            cumul_row_male += total_row_male
            line += 1
        sheet.write(line, 0, 'Total', cumul_label_format)
        col = 1
        for year in year_header:
            sheet.write(line, col, list_country[str(year) + 'female'], cumul_number_format)
            sheet.write(line, col + 1, list_country[str(year) + 'male'], cumul_number_format)
            sheet.write(line, col + 2, list_country[str(year) + 'female'] + list_country[str(year) + 'male'],
                        cumul_number_format)
            col += 3
        i = line + 3

    def generate_xlsx_report(self, workbook, datas, obj):
        country_header = datas['country_header']
        country_lines = datas['country_lines']
        year_header = datas['year_header']
        year_lines = datas['year_lines']
        city_header = datas['city_header']
        city_lines = datas['city_lines']
        total_gross_header = datas['total_gross_header']
        total_gross_lines = datas['total_gross_lines']
        overall_payroll_header = datas['overall_payroll_header']
        overall_payroll_line = datas['overall_payroll_line']

        # countries_data = datas['countries_lines']
        # hiring_date_header = datas['hiring_date']
        sheet = workbook.add_worksheet('Masse salariale')
        tax_contribution_format = workbook.add_format(self.tax_contribution_format)
        social_contribution_format = workbook.add_format(self.social_contribution_format)
        contribution_by_organization_format = workbook.add_format(self.contribution_by_organization_format)
        content_label_format = workbook.add_format(self.content_label_format)
        content_number_format = workbook.add_format(self.content_number_format)
        cumul_label_format = workbook.add_format(self.cumul_label_format)
        cumul_number_format = workbook.add_format(self.cumul_number_format)
        self.formatSheet(sheet)
        titre = 'MASSE SALARIALE PAR PAYS'
        self.generate_header(sheet, titre, country_header, tax_contribution_format)
        self.generate_lines(sheet, country_header, country_lines, content_label_format, content_number_format,
                            cumul_label_format, cumul_number_format)
        titre = "MASSE SALARIALE PAR ANNEE D'EMBAUCHE"
        self.generate_year_header(sheet, titre, year_header, tax_contribution_format)
        self.generate_year_lines(sheet, year_header, year_lines, content_label_format, content_number_format,
                                 cumul_label_format, cumul_number_format)

        titre = "MASSE SALARIALE PAR BRUT TOTAL"
        self.generate_year_header_brut_total(sheet, titre, total_gross_header, tax_contribution_format)
        self.generate_salary_mass_total_brut_lines(sheet, total_gross_header, total_gross_lines, content_label_format,
                                 content_number_format, cumul_label_format, cumul_number_format)

        titre = "MASSE SALARIALE PAR BRUT GLOBAL"
        self.generate_year_global_brut_header(sheet, titre, overall_payroll_header, tax_contribution_format)
        self.generate_year_global_brut_lines(sheet, overall_payroll_header, overall_payroll_line, content_label_format,
                                 content_number_format, cumul_label_format, cumul_number_format)

        workbook.close()
