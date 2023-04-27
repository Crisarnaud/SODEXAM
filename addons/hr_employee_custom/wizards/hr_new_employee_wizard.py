# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from datetime import date

from odoo import api, fields, models, exceptions


class HrNewEmployeesWizard(models.TransientModel):
    _name = 'hr.new.employees.wizard'
    _description = 'HR New employees by period of beginning'

    def _get_default_date_from(self):
        year = fields.Date.from_string(fields.Date.today()).strftime('%Y')
        return '{}-01-01'.format(year)

    def _get_default_date_to(self):
        date = fields.Date.from_string(fields.Date.today())
        return date.strftime('%Y') + '-' + date.strftime('%m') + '-' + date.strftime('%d')

    type = fields.Many2one('hr.leave.type', "Type")
    date_to = fields.Date(string='Au', default=_get_default_date_to)
    date_from = fields.Date(string="De", default=_get_default_date_from)

    def generate_data(self):
        res = []
        employees = self.env['hr.employee'].search([('start_date', '>=', self.date_from),
                                                    ('start_date', '<', self.date_to),
                                                    ('active', '=', True)])
        if employees:
            for emp in employees:
                contrat_empl = self.env['hr.contract'].search([('employee_id', '=', emp.id)])
                gender = ''
                if emp.gender == 'male':
                    gender = 'M'
                elif emp.gender == 'female':
                    gender = 'F'


                val = {
                    'identification_id': emp.identification_id,
                    'cat': contrat_empl.categorie_salariale_id.name or '',
                    'college': emp.category_contract_id.name or '',
                    'name': str(emp.name) + ' ' + str(emp.first_name),
                    'job_id': emp.job_id.name,
                    # 'bureau_id': emp.bureau_id.name or '',
                    'service_id': emp.service_id.description or '',
                    'direction_id': emp.direction_id.description or '',
                    'department_id': emp.department_id.description or '',
                    # 'plateforme_id': emp.plateforme.description or '',
                    'gender': gender,
                    'age': emp.age,
                    'start_date': emp.start_date.strftime('%d/%m/%Y') if emp.start_date else '',
                    'date_anciennete': emp.date_anciennete.strftime('%d/%m/%Y') if emp.date_anciennete else '',
                    'birthday': emp.birthday.strftime('%d/%m/%Y') if emp.birthday else '',
                    'type_contrat': contrat_empl.contract_type_id.name or ''
                }
                res.append(val)
        return res

    def add_hr_manager_signature(self):
        res = []
        emp = self.env['hr.employee'].search([], limit=1)
        val = {
            'manager': str(emp.company_id.hr_manager_id.first_name) + ' ' + str(emp.company_id.hr_manager_id.name)
        }
        res.append(val)
        return res


    def print_report_new_employee_xls(self):
        data = {
            'lines': self.generate_data (),
            'ids': self.id,
            'form': self.read (),
        }
        return self.env.ref ('hr_employee_custom.action_new_employee_xls').report_action (self, data=data)

    def print_report_new_employee_pdf(self):
        data = {'model': self._name, 'form': self.read(), 'new_employee': self.generate_data(),
                'res': self.generate_data(), 'manager': self.add_hr_manager_signature()}
        return self.env.ref('hr_employee_custom.action_new_employee_pdf').report_action(self, data=data)
