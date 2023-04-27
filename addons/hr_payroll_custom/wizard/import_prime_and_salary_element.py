# -*- coding:utf-8 -*-


import time
from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models, exceptions
import xlrd
import base64


class ImportSalaryElement(models.TransientModel):
    _name = 'hr.contract_import_salary'
    _description = "Import salary element"

    type = fields.Selection([('base', 'Salaire base'), ('sursalaire', 'Sursalaire'), ('other', 'Primes')], 'Type ')
    prime_id = fields.Many2one('hr.payroll.prime', 'Prime')
    data_file = fields.Binary("Fichier à import", required=True)

    def _get_compute_data(self, sheet):
        try:
            keys = [sheet.cell(0, col_index).value for col_index in range(sheet.ncols)]

            dict_list = []
            for row_index in range(1, sheet.nrows):
                d = {keys[col_index]: sheet.cell(row_index, col_index).value
                     for col_index in range(sheet.ncols)}
                print(d)
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
                    identification = int(dt['identification_id'])
                    employee = self.env['hr.employee'].search([('identification_id', '=', identification)])
                    if employee and employee.contract_id:
                        if self.type == 'base':
                            employee.contract_id.write({'wage': dt['amount']})
                        elif self.type == 'sursalaire':
                            employee.contract_id.write({'sursalaire': dt['amount']})
                        else:
                            if self.prime_id:
                                prime_montant_obj = self.env['hr.payroll.prime.montant']
                                is_exist = prime_montant_obj.search([('prime_id', '=', self.prime_id.id),
                                                                     ('contract_id', '=', employee.contract_id.id)])
                                if is_exist:
                                    is_exist.unlink()
                                prime_montant_obj.create({
                                    'contract_id': employee.contract_id.id,
                                    'prime_id': self.prime_id.id,
                                    'montant_prime': dt['amount']
                                })
        return True
