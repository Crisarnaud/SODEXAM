# -*- encoding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2021
# Author: Veone
#
# Fichier du module hr_payroll_ci_raport
# ##############################################################################


from odoo import fields, models


class HrPayslipSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    _order = 'sequence'

    rule_doubled = fields.Boolean(string="Règle doublée en cas d'allocation de congé", default=False, store=True,
                                  help="Utilisé pour spécifiée que la règle est doublée en cas de paiement de l'allocation de congés")
    input_ids = fields.One2many('hr.rule.input', 'input_id', string='Inputs', copy=True)
    appears_on_payroll = fields.Boolean(string='Apparaît sur le Livre de paie', default=False,
                                        help="Utilisé pour afficher la règle salariale sur le livre de paie")
    contribution_type = fields.Selection([('tax', 'Fiscale'), ('social', 'Sociale')], string="Type cotisation",
                                         help="Utilisé pour le rapport des cotisations par organisme")
    imputation_type = fields.Selection([('earnings', 'Est un gain'), ('deductions', 'Est une retenue')],
                                       string="Type imputation",
                                       help="Utiliser dans la génération de certains rapports tel que le rapport "
                                            "des cumuls des rubriques par période")
    is_tax_fdfp = fields.Boolean("Est un impôt FDFP")
    overall_payroll_rule = fields.Boolean(string='Utilisé pour la masse salariale globale', default=False,
                                          help="Utilisé pour le calcul de la masse salariale globale")
    natural_advantage = fields.Boolean('Avantage en nature', default=False)
    category_id = fields.Many2one('hr.salary.rule.category', string='Category', required=False)
    use_to_compute_leave = fields.Boolean('Utilisé pour le calcul des congés payés', help="Cochez si cette règle doit "
                                                                                          "être utilisée pour le "
                                                                                          "calcul de l'allocation de "
                                                                                          "congés-payés ")

    def _recursive_search_of_rules(self):
        """
        @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
        """
        children_rules = []
        for rule in self.filtered(lambda rule: rule.child_ids):
            children_rules += rule.child_ids._recursive_search_of_rules()
        return [(rule.id, rule.sequence) for rule in self] + children_rules


class HrSalaryCategorie(models.Model):
    _inherit = 'hr.salary.rule.category'

    type = fields.Selection([('employee', 'Salariale'),
                             ('employer', 'Patronale'),
                             ('other', 'Autres')], string="Type")


class HrRuleInput(models.Model):
    _name = 'hr.rule.input'
    _description = 'Salary Rule Input'

    name = fields.Char(string='Description', required=True)
    code = fields.Char(required=True, help="The code that can be used in the salary rules")
    input_id = fields.Many2one('hr.salary.rule', string='Salary Rule Input', required=True)
