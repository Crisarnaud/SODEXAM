# -*- coding:utf-8 -*-


import time
from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import Warning
import xlrd
import base64
import logging

_logger = logging.getLogger (__name__)


class ImportInputPayslip(models.TransientModel):
    _name = 'hr.payslip.import_input'
    _description = "Import salary element"

    type = fields.Selection([('input', "Données d'entrée"), ('days', 'Jours')], 'Type ', required=True)
    rule_id = fields.Many2one('hr.salary.rule', 'Rubrique')
    data_file = fields.Binary("Fichier à importer", required=True)

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
        list=[]
        data_file = base64.b64decode(self.data_file)
        book = xlrd.open_workbook(file_contents=data_file)
        sheet_names = book.sheet_names()
        run_id = self.env['hr.payslip.run'].search([('id', '=', self.env.context.get('active_id'))])
        if run_id:
            if sheet_names:
                for name in sheet_names:
                    sheet = book.sheet_by_name(name)
                    data = self._get_compute_data(sheet)
                    _logger.info("je suis la %s" ,data)
                    for dt in data:
                        list.append(dt)
                        _logger.info("nous sommes la %s",dt)
                        _logger.info("nous sommes la list.append(dt) %s",list)
                        identification = int(dt['identification_id'])
                        list.append (identification)
                        _logger.info("nous sommes la identification %s",identification)
                        _logger.info("nous sommes la list indentification %s",list)
                        if dt['code'] != self.rule_id.code:
                            raise Warning(_("le code contenu dans le fichier est différent de celui de la règle que "
                                            "vous voulez importer. Merci de faire les corrections nécessaires"))
                        employee = self.env['hr.employee'].search([('identification_id', '=', identification)], limit=1)
                        if employee:
                            _logger.info ("nous sommes la employee %s", employee)
                            payslip = run_id.slip_ids.filtered(lambda s: s.employee_id == employee)
                            if len(payslip) > 1:
                                raise exceptions.ValidationError("L'employé {} {} matricule {} possède plus d'un "
                                                                 "bulletin dans ce lot. Merci de les supprimer et de ne"
                                                                 " garder qu'un seul.".format(employee.name,
                                                                                              employee.first_name,
                                                                                              employee.identification_id
                                                                                              )
                                                                 )
                            if payslip:
                                if self.type == 'input':
                                    input = self.env['hr.payslip.input'].search(
                                        [('payslip_id', '=', payslip.id), ('code', '=', dt['code'])])
                                    if len(input) > 1:
                                        raise exceptions.ValidationError("Le bulletin {} de l'employé {} possède plus "
                                                                         "d'une fois l'entrée {} dans son bulletin."
                                                                         "Merci de les supprimer et de ne garder qu'un "
                                                                         "seul".format(payslip.number, employee.name,
                                                                                       self.rule_id.name))
                                    if input:
                                        input.write({'amount': dt['amount']})
                                    else:
                                        self.env['hr.payslip.input'].create({
                                            'payslip_id': payslip.id,
                                            'code': dt['code'],
                                            'contract_id': payslip.contract_id.id,
                                            'amount': dt['amount'],
                                            'name': self.rule_id.name
                                        })

                                else:
                                    worked_days = self.env['hr.payslip.worked_days'].search(
                                        [('payslip_id', '=', payslip.id), ('code', '=', dt['code'])])
                                    if len(worked_days) > 1:
                                        raise exceptions.ValidationError("Le bulletin {} de l'employé {} possède plus "
                                                                         "d'une fois l'entrée {} dans son bulletin."
                                                                         "Merci de les supprimer et de ne garder qu'un "
                                                                         "seul.".format(payslip.number, employee.name,
                                                                                        self.rule_id.name))
                                    if worked_days:
                                        worked_days.write({
                                            'number_of_days': dt['number_of_days'],
                                            'number_of_hours': dt['number_of_hours']
                                        })
                                    else:
                                        self.env['hr.payslip.worked_days'].create({
                                            'payslip_id': payslip.id,
                                            'code': dt['code'],
                                            'name': self.rule_id.name,
                                            'number_of_days': dt['number_of_days'],
                                            'number_of_hours': dt['number_of_hours'],
                                            'contract_id': payslip.contract_id.id
                                        })
                                payslip.compute_sheet()
            return True
