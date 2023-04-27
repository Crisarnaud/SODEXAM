# -*- coding: utf-8 -*-

from odoo import api, models, osv, fields
# from openerp import osv,fields,models, api
from odoo.tools.translate import _
from datetime import datetime


class ModelContract(models.Model):
    _inherit = "hr.contract"

    Type_employee = [('h', 'Horaire'), ('j', 'Journalier'), ('m', 'Mensuel'), ('p', 'Fonctionnaire')]

    hr_payroll_prime_ids = fields.One2many("hr.payroll.prime.montant", "contract_id", "Primes")
    struct_id = fields.Many2one("hr.payroll.structure", "Structure")
    type = fields.Selection(Type_employee, 'Type', required=False, default=False, related="employee_id.type")


class CategorieSalariale(models.Model):
    _inherit = "hr.categorie.salariale"

    brut_indiciaire = fields.Integer("Brut Indiciaire")


class HrModelContrat(models.Model):
    _inherit = 'hr.model.contract'
    _name = "hr.model.contract"

    structure_salariale = fields.Many2one('hr.payroll.structure', "Structure salariale")
