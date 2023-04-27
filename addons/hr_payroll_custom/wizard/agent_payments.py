# -*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _, tools
from odoo.exceptions import Warning, ValidationError


class AgentPayments(models.TransientModel):
    _name = 'payroll_ci_raport.agent_payments'
    _description = "Rapport des payements par agent"

    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    rules_ids = fields.Many2many('hr.salary.rule', 'rules_agent_payments_rel', 'rules_id', 'agent_payments_id',
                                 string="Règle(s)", domain="[('appears_on_payroll','=',True)]")
    employee_ids = fields.Many2many('hr.employee', 'employee_agent_payments_rel', 'employee_id', 'agent_payments_id',
                                    string="Employé(s)")
    company_id = fields.Many2one('res.company', 'Compagnie', required=True, default=1)

    def get_header(self):
        id_rules = []
        if self.rules_ids:
            for rule in self.rules_ids:
                id_rules.append(rule.id)
            check_rules = ('id', 'in', id_rules)
        else:
            check_rules = (1, '=', 1)

        rules = self.env['hr.salary.rule'].search([check_rules, ('appears_on_payroll', '=', True)])
        rules_list = []
        for rule in rules.sorted(lambda key: key.sequence):
            rules_list.append(rule.name)
        return rules_list

    def get_data(self):
        res = []
        date_from = self.date_from
        date_to = self.date_to

        id_rules = []
        if self.rules_ids:
            for rule in self.rules_ids:
                id_rules.append(rule.id)
            check_rules = ('id', 'in', id_rules)
        else:
            check_rules = (1, '=', 1)

        rules = self.env['hr.salary.rule'].search([check_rules, ('appears_on_payroll', '=', True)])
        if not rules:
            raise ValidationError(_("Aucune règle n'a été configuré. Merci de définir les règles qui doivent "
                                    "apparaitre dans le livre de paie."))
        id_employees = []
        if self.employee_ids:
            for employee in self.employee_ids:
                id_employees.append(employee.id)
            check_employees = ('id', 'in', id_employees)
        else:
            check_employees = (1, '=', 1)
        employees = self.env['hr.employee'].search([check_employees])
        if not employees:
            raise ValidationError(_("Vous n'avez pas d'employé dans votre base. Merci d'en créer avant d'effectuer "
                                    "cette opération."))
        for employee in employees.sorted(lambda key: key.identification_id):
            employee_rec = {
                'employee': str(employee.name) + ' ' + str(employee.first_name),
                'identification': employee.identification_id
            }
            rules_list = []
            for rule in rules.sorted(lambda key: key.sequence):
                rule_item = {'rule': rule.name}
                payslip_lines = self.env['hr.payslip.line'].search([('date_from', '>=', date_from),
                                                                    ('date_to', '<=', date_to),
                                                                    ('salary_rule_id', '=', rule.id),
                                                                    ('employee_id', '=', employee.id),
                                                                    ('company_id', '=', self.company_id.id)])
                cumul_amount = 0
                for line in payslip_lines:
                    cumul_amount += line.total
                rule_item['amount'] = cumul_amount
                rules_list.append(rule_item)
            employee_rec['rules'] = rules_list
            res.append(employee_rec)
        return res

    def print_report_xls(self):
        data = {
            'model': self._name,
            'date_from': self.date_from.strftime("%d/%m/%Y"),
            'date_to': self.date_to.strftime("%d/%m/%Y"),
            'header': self.get_header(),
            'lines': self.get_data()
        }
        return self.env.ref('hr_payroll_custom.action_report_agent_payments_xls').report_action(self, data=data)
