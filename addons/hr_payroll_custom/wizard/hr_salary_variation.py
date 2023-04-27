# -*- coding:utf-8 -*-

from odoo import api, fields, _, models

import time
from datetime import datetime
from datetime import time as datetime_time
from dateutil.relativedelta import relativedelta
from itertools import groupby


class HrSalaryVariation(models.TransientModel):
    _name = 'hr.salary.variation'
    _description = "Hr salary variation"

    date_from = fields.Date(string='Début', required=True)
    date_to = fields.Date(string='Fin', required=True)
    old_date_from = fields.Date(string='Début', required=False)
    old_date_to = fields.Date(string='Fin', required=False)
    rule_ids = fields.Many2many('hr.salary.rule', string="Règle salariale")
    company_id = fields.Many2one("res.company", "Société", default=lambda self: self.env.user.company_id.id)

    def getEmployeePeriode(self):
        employee_ids = []
        slip_obj = self.env['hr.payslip']
        slips = slip_obj.search([('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to),
                                 ('company_id', '=', self.company_id.id)])
        if slips:
            employee_ids = [slip.employee_id.id for slip in slips]
            employee_ids = list(set(employee_ids))
        return employee_ids

    def getCodes(self):
        codes = []
        if self.rule_ids:
            _query = "SELECT code, name FROM hr_salary_rule where id IN %(id_rules)s ORDER BY sequence"
            _params = {
                'id_rules': tuple(self.rule_ids.ids),
            }
            self.env.cr.execute(_query, _params)
        else:
            self.env.cr.execute("SELECT code, name FROM hr_salary_rule ORDER BY sequence")

        codes = {x[0]: x[1] for x in self.env.cr.fetchall()}
        return codes

    def getOldPeriodes(self):
        date_from = str(fields.Date.from_string(self.date_from) + relativedelta(day=1, months=-1))
        date_to = str(fields.Date.from_string(self.date_from) + relativedelta(days=-1))
        self.old_date_from = date_from
        self.old_date_to = date_to

    def getpayslipLinesForPeriode(self, codes, date_from, date_to):
        res = []
        select_query = """
        SELECT emp.id, line.code, line.name, SUM(line.total)
        FROM hr_payslip_line AS line 
        JOIN hr_employee AS emp ON emp.id = line.employee_id
        WHERE line.date_from >= %(date_from)s AND line.date_to <= %(date_to)s AND emp.company_id = %(company_id)s
        GROUP BY salary_rule_id, line.name, line.code, emp.id ORDER BY emp.name
        """

        params_query = {
            'date_from': date_from,
            'date_to': date_to,
            'company_id': self.company_id.id
        }
        self.env.cr.execute(select_query, params_query)
        lines = self.env.cr.dictfetchall()

        for employee_id, data in groupby(lines, lambda l: l['id']):
            employee = self.env['hr.employee'].browse(employee_id)
            val = {
                'employee_id': employee.id,
                'employee_name': employee.name,
                'employee_matricule': employee.identification_id,
            }
            for key in codes.keys():
                val[key] = 0
            data = list(data)
            for dt in data:
                val[dt['code']] = dt['sum']
            res.append(val)
        return res

    def getTotalAmountByCode(self, code, date_from, date_to):
        cmumul = 0
        select_query = """
        SELECT SUM(line.total)
        FROM hr_payslip_line AS line 
        JOIN hr_employee AS emp ON emp.id = line.employee_id
        WHERE line.date_from >= %(date_from)s AND line.date_to <= %(date_to)s AND emp.company_id = %(company_id)s 
        AND code=%(code)s
        GROUP BY salary_rule_id, line.name
        """

        params_query = {
            'date_from': date_from,
            'date_to': date_to,
            'code': code,
            'company_id': self.company_id.id
        }

        self.env.cr.execute(select_query, params_query)
        result = self.env.cr.fetchone()
        if result:
            return result[0]
        return cmumul

    def getVariationByRule(self, codes):
        res = []

        select_query = """
                SELECT  SUM(line.total)
                FROM hr_payslip_line AS line 
                JOIN hr_employee AS emp ON emp.id = line.employee_id
                WHERE line.date_from >= %(date_from)s AND line.date_to <= %(date_to)s AND emp.company_id = %(company_id)s
                 AND code = %(code)s
                GROUP BY salary_rule_id
                """

        for code in codes:
            rule = self.env['hr.salary.rule'].search([('code', '=', code)], limit=1)
            if rule:
                params_query = {
                    'date_from': self.date_from,
                    'date_to': self.date_to,
                    'code': code,
                    'company_id': self.company_id.id
                }

                params_query_2 = {
                    'date_from': self.old_date_from,
                    'date_to': self.old_date_to,
                    'code': code,
                    'company_id': self.company_id.id
                }

                self.env.cr.execute(select_query, params_query)
                new_amount = self.env.cr.fetchone()
                if new_amount is None:
                    new_amount = 0
                else:
                    new_amount = new_amount[0]

                self.env.cr.execute(select_query, params_query_2)
                old_amount = self.env.cr.fetchone()
                if old_amount is None:
                    old_amount = 0
                else:
                    old_amount = old_amount[0]

                ecart = new_amount - old_amount

                val = {
                    'code': rule.code,
                    'name': rule.name,
                    'old_amount': old_amount,
                    'new_amount': new_amount,
                    'ecart': ecart
                }
                res.append(val)

        return res

    def compute_data(self, employee_ids, new_lines, old_lines, codes):
        res = []
        employees = self.env['hr.employee'].browse(employee_ids)
        if employees:
            for employee in employees.sorted(lambda r: r.identification_id):
                val = {
                    'id': employee.id,
                    'name': employee.name,
                    'first_name': employee.first_name,
                    'matricule': employee.identification_id,
                    'line': {key: 0 for key in codes.keys()},
                    'old_line': {key: 0 for key in codes.keys()}
                }
                line = [line for line in new_lines if line['employee_id'] == employee.id]
                if line:
                    for key in codes.keys():
                        val['line'].update(line[0])
                old_line = [line for line in old_lines if line['employee_id'] == employee.id]
                if old_line:
                    val['old_line'].update(old_line[0])
                res.append(val)
        return res

    def export_to_excel(self):
        self.ensure_one()
        context = self.env.context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        emp_ids = self.getEmployeePeriode()
        return self.env.ref('hr_payroll_custom.action_hr_salaryy_recap_print').report_action(self, data=datas,
                                                                                             config=False)

    def export_recap_to_excel(self):
        self.ensure_one()
        context = self.env.context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        emp_ids = self.getEmployeePeriode()
        return self.env.ref('hr_payroll_custom.action_hr_salary_recap_by_rule_print').report_action(self, data=datas,
                                                                                                    config=False)
