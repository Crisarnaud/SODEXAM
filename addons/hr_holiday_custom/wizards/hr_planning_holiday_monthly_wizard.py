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


class HrPlanningMonthlyHoliday(models.TransientModel):
    _name = 'planning.holiday.monthly.wizard'
    _description = 'Planning holidays monthly'

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
        cong = []
        if employees:
            for emp in employees:
                gender = ''
                if emp.gender == 'male':
                    gender = 'M'
                else:
                    if emp.gender == 'female':
                        gender = 'F'
                leave = self.env['hr.leave'].search([
                    ('employee_id.id', '=', emp.id),
                    ('state', '=', 'validate'),
                    ('holiday_status_id.id', '=', self.holiday_type_id.id),
                ])
                cong.append(leave)

                previous_year = datetime.now() + relativedelta(years=-1)
                previous_stock = self.env['save.stock.holiday'].search(
                    [('name', '=', previous_year.year), ('employee_id', '=', emp.id)], limit=1).number_days
                val = {
                    'identification_id': emp.identification_id,
                    'name': str(emp.name) + ' ' + str(emp.first_name),
                    'job_id': emp.job_id.name,
                    'leaves_count': emp.leaves_count,
                    'department_id': emp.department_id.description,
                    'direction_id': emp.direction_id.description,
                    'number_days_estimed_holidays': emp.number_days_estimed_holidays or '',
                    'stock_holiday': previous_stock or '',
                    'total': previous_stock + emp.number_days_estimed_holidays,
                    'gender': gender or '',
                }
                res.append(val)
        return res

    def get_data_from_leave(self):
        leaves = self.env['hr.leave'].search([('holiday_status_id.id', '=', self.holiday_type_id.id),
                                              ('state', '=', 'validate')])
        result = []
        durees = []
        if leaves:
            for cong in leaves:
                durees.append(cong.number_of_days_display)
                vals = {
                    'date_from': cong.request_date_from.strftime('%b-%Y') if cong.request_date_from else '',
                    'intention_to_holiday': cong.number_of_days_display,
                    'id': cong.employee_id.identification_id,
                    'name': cong.employee_id.name,
                }
                result.append(vals)
        return result

    def add_hr_manager_signature(self):
        res = []
        emp = self.env['hr.employee'].search([], limit=1)
        val = {
            'manager': str(emp.company_id.hr_manager_id.first_name) + ' ' + str(emp.company_id.hr_manager_id.name),
            'dg': str(emp.company_id.general_manager_id.name) + ' ' + str(emp.company_id.general_manager_id.first_name),
        }
        res.append(val)
        return res

    def get_last_year(self):
        res = []
        val = {
            'last_date': (date.today() - relativedelta(years=1)).strftime('%Y')
        }
        res.append(val)
        return res

    def print_report_xls(self):
        data = {
            'lines': self.generate_data(),
            'ids': self.id,
            'form': self.read(),
        }
        return self.env.ref('hr_holiday_custom.action_planning_holiday_monthly_employee_xls').report_action(self, data=data)

    def print_report_pdf(self):
        locale = self.env.context.get('lang') or 'en_US'
        data = {'model': self._name, 'form': self.read(),
                'res': self.generate_data(),
                'conges': self.get_data_from_leave(),
                'manager': self.add_hr_manager_signature(),
                'last_date': self.get_last_year(),
                'date': tools.ustr(
                    babel.dates.format_date(date=date.today(), format='dd MMMM y', locale=locale))
                }
        return self.env.ref('hr_holiday_custom.action_planning_holiday_monthly_employee_pdf').report_action(self, data=data)
