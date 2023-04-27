# -*- coding:utf-8 -*-


from odoo import api, fields, models, _


class AccountMoveTemplate(models.Model):
    _name = "account.move_template"
    _description = "Template "

    name = fields.Char("Libellé", required=True)
    active = fields.Boolean("Actif(ve)", default=True)
    sequence = fields.Integer("Sequence", default=1)
    line_ids = fields.One2many("account.move_template.line", 'template_id', "Lignes", required=True)
    journal_id = fields.Many2one("account.journal", "Journal")


class AccountMoveTemplateLine(models.Model):
    _name = "account.move_template.line"
    _description = "Lignes du model"

    account_id = fields.Many2one("account.account", "Compte comptable", required=True)
    rule_ids = fields.Many2many('hr.salary.rule', 'account_salary_rule_real', 'line_id', 'rule_id', 'Règle salariale',
                                required=True)
    name = fields.Char("Libellé", required=True)
    type = fields.Selection([('debit', 'Débit'), ('credit', 'Crédit')], string="Nature", default=False)
    template_id = fields.Many2one("account.move_template", "Template", required=False)

