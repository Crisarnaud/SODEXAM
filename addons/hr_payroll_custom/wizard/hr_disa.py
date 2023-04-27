# -*- coding:utf-8 -*-

from odoo import api, fields, _, models


import time
from datetime import datetime
from datetime import time as datetime_time
from dateutil import relativedelta


class HrDISA(models.TransientModel):
    _name ='hr.disa'
    _description = "Gestion des etats disa"

    date_from = fields.Date(string='Date From', required=True, default=time.strftime('%Y-01-01'))
    date_to = fields.Date(string='Date To', required=True, default=time.strftime('%Y-12-31'))
    company_id = fields.Many2one("res.company", "Société", default=lambda self: self.env.user.company_id.id)

    def computeDisa(self):
        res = []
        employees = self.env['hr.employee'].search([('company_id', '=', self.company_id.id),
                ('type', '=', ('m', 'j', 'm'))], order= 'identification_id')
        if employees:
            num_order = 0
            for emp in employees:
                type = 'M'
                if emp.type == 'j':
                    type = 'J'
                else:
                    type = 'H'
                print(emp.name)
                val = {
                    'order': num_order + 1,
                    'employee_name': emp.name+' '+emp.first_name,
                    'num_cnps': emp.identification_cnps,
                    'date_naissance': emp.birthday,
                    'date_embauche': emp.start_date,
                    'date_depart': emp.end_date or '',
                    'type_employee': type,
                    'temps_travail': emp.getTotalRubriqueByPeriod('WORK100', self.date_from, self.date_to),
                    'brut_total': emp.getTotalRubriqueByPeriod('BRUT', self.date_from, self.date_to),
                    'brut_autre': emp.getAmountRubriqueByPeriod('BACT_PF', self.date_from, self.date_to),
                    'brut_cnps': emp.getAmountRubriqueByPeriod('CNPS', self.date_from, self.date_to),
                    'cotisation': '1234',
                    'comment': ""
                }
                res.append(val)
        print(res)
        return res

    def export_to_excel(self):
        data = {}
        context = self.env.context
        self.ensure_one()
        print(self.id)
        data['lines'] = self.computeDisa()
        data['ids'] = self.id
        data['model'] = self._name
        return self.env.ref('hr_payroll_custom.action_raport_hr_disa').report_action(self, data=data)
