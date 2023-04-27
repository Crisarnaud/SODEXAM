# -*- coding:utf-8 -*-

from odoo import api, fields, models, exceptions, _
import xlrd
import base64


class ImportAdvantages(models.TransientModel):
    _name = 'hr_disa.import_advantages'
    _description = 'Importer les avantages (Nature et espèce)'

    data_file = fields.Binary("Fichier à import", required=True)

    def _get_compute_data(self, sheet):
        try:
            keys = [sheet.cell(0, col_index).value for col_index in range(sheet.ncols)]

            dict_list = []
            for row_index in range(1, sheet.nrows):
                d = {keys[col_index]: sheet.cell(row_index, col_index).value
                     for col_index in range(sheet.ncols)}
                dict_list.append(d)
            return dict_list
        except:
            return False

    def compute_data(self):
        data_file = base64.b64decode(self.data_file)
        book = xlrd.open_workbook(file_contents=data_file)
        sheet_names = book.sheet_names()
        if sheet_names:
            for name in sheet_names:
                sheet = book.sheet_by_name(name)
                data = self._get_compute_data(sheet)
                for dt in data:
                    identification = dt['identification_id']
                    id_employee = self.env['hr.employee'].search([('identification_id', '=', identification)],
                                                                 limit=1).id
                    record_employe = self.env['hr_disa.payroll_disa_line'].search([('employee_id', '=', id_employee),
                                                                                   ('disa_id', '=',
                                                                                    self._context.get('active_id'))])
                    if record_employe:
                        record_employe.natural_advantage = dt['natural_advantage']
                    else:
                        pass
