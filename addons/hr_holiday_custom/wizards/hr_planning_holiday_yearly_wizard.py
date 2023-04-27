# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
import datetime
from datetime import date, datetime
from odoo import api, fields, models, exceptions
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from odoo import tools
import babel


class HrPlanningYearlyHoliday(models.TransientModel):
    _name = 'planning.holiday.yearly.wizard'
    _description = 'Planning holidays yearly'

    all_dirs = fields.Boolean(string="Toutes les directions")
    # direction_ids = fields.Many2many('hr.department', string='Direction(s)', domain=[('type', '=', 'direction')])
    gender = fields.Selection([('male', 'M'), ('female', 'F')], string='Genre')
    all_gender = fields.Boolean(string="Tous les genres")
    holiday_type_id = fields.Many2one('hr.leave.type', string="Type de congés",
                                      default=lambda self: self.env['hr.leave.type'].search([('code', '=', 'CONG')]))
    department_ids = fields.Many2many('hr.department', string='Département(s)', domain=[('type', '=', 'department')])
    all_depts = fields.Boolean(string="Tous les départements")

    def generate_data(self):
        dir_rc = []
        if self.all_dirs or not self.department_ids:
            if self.department_ids.type == 'direction':
                dir = (1, '=', 1)
        else:
            if self.department_ids and self.department_ids.type == 'direction':
                for dir in self.department_ids:
                    dir_rc.append(dir.id)
                dir = ('direction_id', 'in', dir_rc)

        if self.all_depts or not self.department_ids:
            dep = (1, '=', 1)
        else:
            for dep in self.department_ids:
                dir_rc.append(dep.id)
            dep = ('department_id', 'in', dir_rc)

        if self.all_gender or not self.gender:
            gend = (1, '=', 1)

        else:
            gend = ('gender', '=', self.gender)

        employees = self.env['hr.employee'].search([dep, gend],
                                                   order="identification_id asc, direction_id asc, department_id asc")

        res = []
        if employees:
            for employee in employees:
                gender = ''
                if employee.gender == 'male':
                    gender = 'M'
                else:
                    if employee.gender == 'female':
                        gender = 'F'
                previous_year = datetime.now() + relativedelta(years=-1)
                previous_stock = self.env['save.stock.holiday'].search(
                    [('name', '=', previous_year.year), ('employee_id', '=', employee.id)], limit=1).number_days
                val = {
                    'identification_id': employee.identification_id,
                    'name': str(employee.name) + ' ' + str(employee.first_name),
                    'job_id': employee.job_id.name,
                    'number_days_estimed_holidays': employee.number_days_estimed_holidays or '',
                    'department_id': employee.department_id.description or '',
                    'direction_id': employee.direction_id.description or '',
                    'estimed_date_leave': str(
                        employee.estimed_date_leave.strftime('%b-%Y')) if employee.estimed_date_leave else '',
                    'stock_total_holiday': employee.stock_total_holiday if employee.stock_total_holiday else '',
                    'stock_holiday': previous_stock or '',
                    'total': previous_stock + employee.number_days_estimed_holidays,
                    'gender': gender or '',
                }
                res.append(val)
        return res

    def get_data_from_leave(self):
        holiday_planning = self.env['hr.holiday.planning'].search([('state', '=', 'done')])
        result = []
        durees = []
        if holiday_planning:
            for cong in holiday_planning:
                durees.append(cong.number_of_days)
                vals = {
                    'date_from': cong.date_from.strftime('%b-%Y') if cong.date_from else '',
                    'intention_to_holiday': cong.number_of_days,
                    'id': cong.employee_id.identification_id,
                    'name': cong.employee_id.name,
                }
                result.append(vals)
        return result

    def get_last_year(self):
        res = []
        val = {
            'last_date': (date.today() - relativedelta(years=1)).strftime('%Y')
        }
        res.append(val)
        return res

    def add_hr_manager_signature(self):
        res = []
        emp = self.env['hr.employee'].search([], limit=1)
        val = {
            'manager': str(emp.company_id.hr_manager_id.first_name) + ' ' + str(emp.company_id.hr_manager_id.name),
            'dg': str(emp.company_id.general_manager_id.name) + ' ' + str(emp.company_id.general_manager_id.first_name),
        }
        res.append(val)
        return res

    def print_report_xls(self):
        data = {
            'lines': self.generate_data(),
            'ids': self.id,
            'form': self.read()
        }
        return self.env.ref('hr_holiday_custom.action_planning_holiday_yearly_employee_xls').report_action(self,
                                                                                                           data=data)

    def print_report_pdf(self):
        locale = self.env.context.get('lang') or 'en_US'
        data = {'model': self._name, 'form': self.read(), 'new_employee': self.generate_data(),
                'res': self.generate_data(), 'manager': self.add_hr_manager_signature(),
                'conges': self.get_data_from_leave(),
                'last_date': self.get_last_year(), 'date': tools.ustr(
                babel.dates.format_date(date=date.today(), format='dd MMMM y', locale=locale))}
        return self.env.ref('hr_holiday_custom.action_planning_holiday_yearly_employee_pdf').report_action(self,
                                                                                                           data=data)
