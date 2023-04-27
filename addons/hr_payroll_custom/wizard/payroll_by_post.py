# -*- coding:utf-8 -*-

from odoo import fields, models, api, _, tools
from odoo.exceptions import Warning


class PayrollByPost(models.TransientModel):
    _name = 'payroll_ci_raport.payroll_by_post'
    _description = "Gestion des rubriques de paie par poste et periode"

    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    rule_id = fields.Many2one('hr.salary.rule', 'Règle', required=False, domain="[('appears_on_payroll','=',True)]")
    company_id = fields.Many2one('res.company', 'Compagnie', required=True, default=1)

    def compute_cumulative_amount(self):
        code = self.rule_id.code
        date_from = self.date_from
        date_to = self.date_to
        employees = self.env['hr.employee'].search([])
        payslip = self.env['hr.payslip']
        res = []
        if not self.rule_id.imputation_type:
            raise Warning(_("Cette règle n'est pas considérée comme un gain ou une retenue. Merci de le spécifier "
                            "dans les paramètres des règles salariales."))

        for employee in employees.sorted(key=lambda r: r.identification_id):
            number_payslips = self.env['hr.payslip'].search_count([('date_from', '>=', date_from),
                                                                   ('date_to', '<=', date_to),
                                                                   ('employee_id', '=', employee.id)])
            if number_payslips >= 1:
                rate = number_payslips
            else:
                continue
            cumulative_rule_amount = payslip.getCumulDataByCode(employee.id, code, date_from, date_to, 'amount')
            if cumulative_rule_amount > 0:
                cumulative_rule_total_amount = payslip.cumulBYCode(employee.id, code, date_from, date_to)
                cumulative_rule_quantity = payslip.getCumulDataByCode(employee.id, code, date_from, date_to, 'quantity')
                cumulative_rule_rate = payslip.getCumulDataByCode(employee.id, code, date_from, date_to, 'rate')
                vals = {
                    'matricule': employee.identification_id,
                    'full_name': employee.name + ' ' + employee.first_name if employee.first_name else employee.name,
                    'base': cumulative_rule_amount,
                    'quantity': cumulative_rule_quantity,
                    'taux': cumulative_rule_rate / rate,
                    'amount': cumulative_rule_total_amount,
                    'imputation_type': self.rule_id.imputation_type
                }
                res.append(vals)
            else:
                continue
        return res

    def get_period_print_report(self):
        detail = []
        vals = {
            'date_from': self.date_from.strftime('%d/%m/%Y'),
            'date_to': self.date_to.strftime('%d/%m/%Y'),
            'rubrique': self.rule_id.sequence,
            'rule_id': self.rule_id.name,
        }
        detail.append(vals)
        return detail

    def print_report_pdf(self):
        data = {
            'model': self._name,
            'form': self.read(),
            'res': self.compute_cumulative_amount(),
            'details_report': self.get_period_print_report(),
        }
        return self.env.ref('hr_payroll_custom.action_report_payroll_by_post_pdf').report_action(self, data=data)

    def print_report_xls(self):
        data = {
            'model': self._name,
            'form': self.read(),
            'res': self.compute_cumulative_amount(),
            'details_report': self.get_period_print_report()
        }
        return self.env.ref('hr_payroll_custom.action_report_payroll_by_post_xls').report_action(self, data=data)
