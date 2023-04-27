# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models, exceptions, _
import datetime


class HrPayrollBudget(models.Model):
    _name = "hr.payroll.budget"
    _description = "Budget Analysis"
    _rec_name = 'name'

    name = fields.Char('Exercice', required=True)
    salary_rules_ids = fields.One2many('hr.payroll.budget.line', 'budget_id', string='Règle salariale')
    state = fields.Selection([('draft', 'Brouillon'),
                              ('done', 'Validé')], default='draft', string='Etape')

    def action_submit(self):
        """
        Valider un budget
        :return:
        """
        for rec in self:
            rec.state = 'done'


class HrSalaryRuleInherit(models.Model):
    _name = "hr.payroll.budget.line"
    _description = "Budget Line"
    _rec_name = 'budget_id'

    budget_id = fields.Many2one('hr.payroll.budget', string='Budget')
    rule_id = fields.Many2one('hr.salary.rule', 'Règle')
    state = fields.Selection('Etat', related='budget_id.state', store=True)
    the_code = fields.Char('Code', related='rule_id.code', store=True)
    name = fields.Char('Code', related='rule_id.name', store=True)
    budget = fields.Float('Budget')
    budget_realized = fields.Float('Montant réalisé', compute='_get_budget_realized', store=True)
    rate = fields.Float('Taux', compute='_get_rate', store=True)
    obs = fields.Char('OBS')

    _sql_constraints = [('name_uniq', 'unique (name)',
                         'Vous avez déjà choisi cette règle !')]

    @api.onchange('rule_id')
    def _get_budget_realized(self):
        """
        Compute realized budget
        :return:
        """
        for rec in self:
            payslip = self.env['hr.payslip.line'].search([('code', '=', rec.the_code)], limit=1)
            if payslip:
                rec.budget_realized = payslip.total

    @api.depends('budget', 'budget_realized')
    def _get_rate(self):
        for rec in self:
            if rec.budget != 0 and rec.budget_realized != 0:
                rec.rate = round((rec.budget_realized * 100) / rec.budget, 2)
            else:
                rec.rate = 0
