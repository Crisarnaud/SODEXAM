# -*- coding:utf-8 -*-

from odoo import api, fields, _, models
from odoo.exceptions import UserError, Warning

import time
from datetime import datetime
from datetime import time as datetime_time
from dateutil.relativedelta import relativedelta
from itertools import groupby


class HrSalaryEmployeeVariation(models.Model):
    _name = 'hr.salary.employee.variation'
    _description = "Hr salary employee variation"

    name = fields.Char("Libellé", required=True)
    date_from = fields.Date(string='Début', required=True)
    date_to = fields.Date(string='Fin', required=True)
    old_date_from = fields.Date(string='Début', required=False)
    old_date_to = fields.Date(string='Fin', required=False)
    company_id = fields.Many2one("res.company", "Société", default=lambda self: self.env.user.company_id.id)
    total_previous_salary = fields.Integer("Total effectif payé mois précedent")
    total_salary = fields.Integer("Effectif total à payer")
    salaries_out = fields.Integer("Employés sortis")
    salaries_in = fields.Integer("Employés entrés")
    total_salary = fields.Integer("Total effectif payé mois en cours")
    employee_ids = fields.One2many("hr.salary.employee.variation_line", "variation_id",
                                   "Liste des employés Entrée/sortie")

    def getOldPeriodes(self):
        date_from = str(fields.Date.from_string(self.date_from) + relativedelta(day=1, months=-1))
        date_to = str(fields.Date.from_string(self.date_from) + relativedelta(days=-1))
        self.old_date_from = date_from
        self.old_date_to = date_to

    def getEmployeesByPeriode(self, date_from, date_to):
        res = []
        select_query = """
                SELECT 
                    employee_id
                FROM 
                    hr_payslip 
                WHERE 
                    date_from >= %(date_from)s AND date_to <= %(date_to)s AND company_id = %(company_id)s
                """

        params_query = {
            'date_from': date_from,
            'date_to': date_to,
            'company_id': self.company_id.id
        }
        self.env.cr.execute(select_query, params_query)
        slip_ids = [x[0] for x in self.env.cr.fetchall()]
        return slip_ids

    def getLines(self, emp_ids, type):
        res = []
        if emp_ids:
            for emp_id in emp_ids:
                val = {
                    'employee_id': emp_id,
                    'type': type,
                }
                res.append(val)
        return res

    def action_compute(self):
        self.employee_ids.unlink()
        self.getOldPeriodes()
        employees = self.getEmployeesByPeriode(self.date_from, self.date_to)
        self.total_salary = len(employees)
        old_employes = self.getEmployeesByPeriode(self.old_date_from, self.old_date_to)
        self.total_previous_salary = len(old_employes)
        result = set(employees) - set(old_employes)
        emp_out = [item for item in old_employes if item not in employees]
        emp_in = [item for item in employees if item not in old_employes]
        self.salaries_out = len(emp_out)
        self.salaries_in = len(emp_in)
        empl_ids = self.getLines(emp_in, 'in') + self.getLines(emp_out, 'out')
        self.employee_ids = self.employee_ids.create(empl_ids)
        return True


class HrSalaryEmployeeVariationLine(models.Model):
    _name = 'hr.salary.employee.variation_line'
    _description = "Hr salary employee variation line"

    employee_id = fields.Many2one("hr.employee", "Employé", required=True)
    name = fields.Char("NOM & PRENOMS", related="employee_id.name")
    identification_id = fields.Char("MATRICULE", related="employee_id.identification_id")
    observation = fields.Text("Observation", required=False)
    variation_id = fields.Many2one("hr.salary.employee.variation", "Variation")
    type = fields.Selection([('in', 'Entrée'), ('out', 'Sortie')], "Type")
