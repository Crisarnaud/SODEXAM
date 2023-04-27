# -*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _, tools
from odoo.exceptions import Warning, ValidationError


class ContributionsByOrganization(models.TransientModel):
    _name = 'payroll_ci_raport.contributions_by_organization'
    _description = "Rapport des cotisations par organisme"

    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    rules_ids = fields.Many2many('hr.salary.rule', 'rules_contributions_by_organization_rel', 'rules_id',
                                 'contributions_by_organization_id', string="Règle(s)",
                                 domain="[('appears_on_payroll','=',True)]")
    company_id = fields.Many2one('res.company', 'Compagnie', required=True, default=1)

    def get_month(self):
        date_from = self.date_from
        date_to = self.date_to
        months = []
        if date_from > date_to:
            raise ValidationError(_("La date de début ne peut pas être supérieur à la date de fin. Merci de faire les "
                                    "corrections nécessaires."))
        if date_from.month == date_to.month:
            months.append(date_to.strftime('%B'))
            months.append('CUMUL PERIODE')
        else:
            months.append(date_from.strftime('%B'))
            delta_month = date_to.month - date_from.month
            date_f = date_from + relativedelta(months=1)
            for mt in range(delta_month):
                months.append(date_f.strftime('%B'))
                date_f += relativedelta(months=1)
            months.append('CUMUL PERIODE')
        return months

    def get_cumulative(self):
        res = []
        date_from = self.date_from
        date_to = self.date_to
        several_months = False
        if date_to.month - date_from.month > 0:
            several_months = True
        rules_list = []
        if self.rules_ids:
            for rule in self.rules_ids:
                rules_list.append(rule.id)
            check_rules = ('id', 'in', rules_list)
        else:
            check_rules = (1, '=', 1)

        rules = self.env['hr.salary.rule'].search(
            [check_rules, '|', ('contribution_type', '=', 'tax'), ('contribution_type', '=', 'social')])

        if not several_months:
            for rule in rules.sorted(lambda key: key.sequence):
                month_amount = {}
                cumulative_amount = []
                payslip_lines = self.env['hr.payslip.line'].search([('date_from', '>=', date_from),
                                                                    ('date_to', '<=', date_to),
                                                                    ('salary_rule_id', '=', rule.id),
                                                                    ('company_id', '=', self.company_id.id)])
                cumul_amount = 0
                for line in payslip_lines:
                    cumul_amount += line.total

                month_amount['month'] = date_from.strftime('%B')
                month_amount['amount'] = cumul_amount
                cumulative_amount.append(month_amount)
                vals = {
                    'rule_name': rule.name,
                    'contribution_type': rule.contribution_type,
                    'category_type': rule.category_id.type,
                    'month_amount': cumulative_amount
                }
                res.append(vals)
        else:
            for rule in rules.sorted(lambda key: key.sequence):
                date_start = date_from
                date_end = date_from + relativedelta(months=1, days=-1)
                cumulative_amount = []
                for mt in range(date_to.month - date_from.month + 1):
                    month_amount = {}
                    payslip_lines = self.env['hr.payslip.line'].search([('date_from', '>=', date_start),
                                                                        ('date_to', '<=', date_end),
                                                                        ('salary_rule_id', '=', rule.id),
                                                                        ('company_id', '=', self.company_id.id)])
                    cumul_amount = 0
                    for line in payslip_lines:
                        cumul_amount += line.total
                    month_amount['month'] = date_start.strftime('%B')
                    month_amount['amount'] = cumul_amount
                    cumulative_amount.append(month_amount)
                    date_start = date_start + relativedelta(months=1)
                    date_end = date_start + relativedelta(months=1, days=-1)

                vals = {
                    'rule_name': rule.name,
                    'contribution_type': rule.contribution_type,
                    'category_type': rule.category_id.type,
                    'month_amount': cumulative_amount,
                }
                res.append(vals)
        return res

    def print_report_xls(self):
        data = {
            'model': self._name,
            'date_from': self.date_from.strftime("%d/%m/%Y"),
            'date_to': self.date_to.strftime("%d/%m/%Y"),
            'months': self.get_month(),
            'lines': self.get_cumulative()
        }
        return self.env.ref('hr_payroll_custom.action_report_contribution_by_organization').report_action(self,
                                                                                                             data=data)
