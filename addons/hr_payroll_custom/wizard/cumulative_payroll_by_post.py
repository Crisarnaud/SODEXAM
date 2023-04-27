# -*- coding:utf-8 -*-

import logging
from odoo import fields, models, api, _, tools
from odoo.exceptions import Warning, ValidationError

_logger = logging.getLogger(__name__)


class CumulativePayrollByPost(models.TransientModel):
    _name = 'payroll_ci_raport.cumulative_payroll_by_period'
    _description = "Cumul des rubriques de paie par periode"

    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    rules_ids = fields.Many2many('hr.salary.rule', 'rules_cumul_by_period_rel', 'rules_id', 'cumul_by_period_id',
                                 string="Règle(s)", domain="[('appears_on_payroll','=',True)]")
    company_id = fields.Many2one('res.company', 'Compagnie', required=True, default=1)

    def get_cumulative_by_period(self):
        res = []
        date_from = self.date_from
        date_to = self.date_to
        rules_list = []
        if self.rules_ids:
            for rule in self.rules_ids:
                rules_list.append(rule.id)
            check_rules = ('id', 'in', rules_list)
        else:
            check_rules = (1, '=', 1)

        rules = self.env['hr.salary.rule'].search([check_rules, ('appears_on_payroll', '=', True)])
        for rule in rules.sorted(lambda key: key.sequence):
            payslip_lines = self.env['hr.payslip.line'].search([('date_from', '>=', date_from),
                                                                ('date_to', '<=', date_to),
                                                                ('salary_rule_id', '=', rule.id),
                                                                ('company_id', '=', self.company_id.id)])
            cumul_amount = 0
            cumul_base = 0
            for line in payslip_lines:
                if line.total > 0:
                    cumul_amount += line.total
                    cumul_base += line.amount
                else:
                    continue
            vals = {
                'sequence': rule.sequence,
                'rule_name': rule.name,
                'base': cumul_base,
                'amount': cumul_amount,
                'imputation_type': rule.imputation_type,
                'type': rule.category_id.type
            }
            if vals['base'] > 0:
                res.append(vals)
            else:
                continue
        return res

    # def get_period_print_report(self):
    #     detail = []
    #     vals = {
    #         'date_from': self.date_from.strftime('%d/%m/%Y'),
    #         'date_to': self.date_to.strftime('%d/%m/%Y'),
    #         'rules': '',
    #         'departments': '',
    #     }
    #     detail.append(vals)
    #     return detail

    def print_report_pdf(self):
        data = {
            'model': self._name,
            'form': self.read(),
            'lines': self.get_cumulative_by_period(),
            'date_from': self.date_from.strftime("%d/%m/%Y"),
            'date_to': self.date_to.strftime("%d/%m/%Y"),
        }
        return self.env.ref('hr_payroll_custom.action_report_cumul_payroll_by_period_pdf').report_action(self,
                                                                                                            data=data)

    def print_report_xls(self):
        data = {
            'model': self._name,
            'date_from': self.date_from.strftime("%d/%m/%Y"),
            'date_to': self.date_to.strftime("%d/%m/%Y"),
            'lines': self.get_cumulative_by_period()
        }
        return self.env.ref('hr_payroll_custom.action_report_payroll_by_period').report_action(self, data=data)
