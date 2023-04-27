# -*- coding:utf-8 -*-

from odoo import api, models, fields, _


class HrFDFPConfig(models.Model):
    _name = "hr.fdfp.config"
    _description = "hr.fdfp.config"
    _rec_name = "rule_id"

    rule_id = fields.Many2one('hr.salary.rule', 'Règle salariale', domain="[('is_tax_fdfp', '=', True)]")
    taux = fields.Float("Taux")
    sequence = fields.Integer("Sequence", default=10)
    active = fields.Boolean("Actif", default=True)