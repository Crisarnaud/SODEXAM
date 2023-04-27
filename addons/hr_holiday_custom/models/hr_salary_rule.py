# -*- encoding: utf-8 -*-

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    amount_python_compute = fields.Text(string='Python Code',
                                        default='''
                        # Available variables:
                        #----------------------
                        # payslip: object containing the payslips
                        # employee: hr.employee object
                        # contract: hr.contract object
                        # rules: object containing the rules code (previously computed)
                        # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                        # worked_days: object containing the computed worked days.
                        # inputs: object containing the computed inputs.
                        # leave: object containing the leaves

                        # Note: returned value have to be set in the variable 'result'

                        result = contract.wage * 0.10''')
    condition_python = fields.Text(string='Python Condition', required=True,
                                   default='''
    # Available variables:
    #----------------------
    # payslip: object containing the payslips
    # employee: hr.employee object
    # contract: hr.contract object
    # rules: object containing the rules code (previously computed)
    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
    # worked_days: object containing the computed worked days
    # inputs: object containing the computed inputs.
    # leave: object containing the leaves

    # Note: returned value have to be set in the variable 'result'

    result = rules.NET > categories.NET * 0.10''',
                                   help='Applied this rule for calculation if condition is true. You can specify condition like basic > 1000.')
    rule_doubled = fields.Boolean(string="Règle doublée en cas d'allocation de congé", default=False, store=True,
                                  help="Utilisé pour spécifiée que la règle est doublée en cas de paiement de l'allocation de congés")
