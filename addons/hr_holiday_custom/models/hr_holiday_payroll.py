import calendar
import logging
import time
from datetime import date
from datetime import datetime, time
from datetime import timedelta
from dateutil import relativedelta
from calendar import monthrange

from odoo import netsvc
from odoo import fields, osv, api, models
from odoo import tools
from odoo.tools.translate import _
from odoo.exceptions import Warning, ValidationError, UserError

from odoo.tools.safe_eval import safe_eval as eval
from decimal import Decimal
from collections import namedtuple
from math import fabs, ceil
from odoo.tools import format_amount, format_date, date_utils

import babel

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.depends('employee_id')
    def _compute_holiday_id(self):
        """Obtenir id du congé sur la fiche salariale
        :return:
        """
        leave_to_pay = self.env['hr.leave'].search([('state', '=', 'validate'), ('to_pay', '=', True), ('payslip_status', '=', False), ('employee_id', '=', self.employee_id.id)], limit=1)
        leave_paid = self.env['hr.leave'].search([('state', '=', 'validate'), ('to_pay', '=', False), ('payslip_status', '=', True), ('employee_id', '=', self.employee_id.id)], limit=1)
        if leave_to_pay:
            if self.date_from.year == leave_to_pay.date_from.year:
                self.holiday_id = leave_to_pay.id
        else:
            if leave_paid:
                if self.date_from.year == leave_paid.date_from.year and self.date_from.month == leave_paid.date_from.month + 1:
                    self.holiday_id = leave_paid.id
                else:
                    pass

    holiday_id = fields.Many2one('hr.leave', 'Congé', store=True)

    def _get_payslip_lines(self):
        """
        Affiche les lignes de rubriques dans le rapport de fiche de paie
        :return:
        """
        res = super(HrPayslip, self)._get_payslip_lines()
        rd = []
        codes = []
        leaves = self.env['hr.leave'].search(
            [('state', '=', 'validate'), ('to_pay', '=', True), ('payslip_status', '=', False),
             ('holiday_status_id.code', '=', 'CONG'),
             ('employee_id', '=', self.employee_id.id)], limit=1)
        leave_already_taken = self.env['hr.leave'].search(
            [('state', '=', 'validate'), ('to_pay', '=', False), ('payslip_status', '=', True),
             ('holiday_status_id.code', '=', 'CONG'),
             ('employee_id', '=', self.employee_id.id)], limit=1)
        cong = self.env['hr.salary.rule'].search([('code', '=', 'CONG')], limit=1)
        rules_doubled = self.env['hr.salary.rule'].search([('rule_doubled', '=', True)])
        for doubled in rules_doubled:
            rd.append(doubled.id)
        for r in res:
            codes.append(r['code'])
            if leaves:
                if r['salary_rule_id'] in rd and cong.code in codes:
                    r['amount'] = r['amount'] * 2
                else:
                    r['amount'] = r['amount']
        # create/overwrite the rule in the temporary results
            if leave_already_taken:
                if leave_already_taken.request_date_from.year == self.date_from.year and self.date_from.month == leave_already_taken.request_date_from.month:
                    r['amount'] = 0
        return res

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        input_ret_syn = self.env['hr.salary.rule'].search([('code', '=', 'RET_SYN')], limit=1)
        payslips = self.search([('employee_id', '=', self.employee_id.id), ('state', '=', 'done')])
        inputs = []
        """
        La retenue synadexam se calcule une seule fois dans l'année.
        Une recherche sera faite dans toutes les fiche de paie de l'année. Si l'input existe déjà,
        cela signifiera que la cotisation a déjà été prélévée, l'input va alors changer le montant et le mettre à zero
        """
        for contract in contracts:
            input = {
                'name': "RETENUE SYNADEXAM",
                'code': input_ret_syn.code,
                'amount': input_ret_syn.amount_fix,
                'salary_rule_id': input_ret_syn.id,
                'contract_id': contract.id,
            }
            res += [input]
            for pay in payslips:
                if pay.date_from.year == self.date_from.year:
                    for inp in pay.input_line_ids:
                        for i in inp:
                            inputs.append(i.code)
                            if str(input_ret_syn.code) in inputs:
                                for r in res:
                                    if r.get('code') == input_ret_syn.code:
                                        r['amount'] = 0
                                        res.remove(r)
        return res
