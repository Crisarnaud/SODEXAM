# -*- encoding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2012 Veone - support.veone.net
# Author: Veone
#
# Fichier du module hr_emprunt
# ##############################################################################  -->
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'
    _order = 'registration_number, number'

    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    journal_id = fields.Many2one('account.journal', 'Journal des salaires', readonly=False, required=False,
                                 default=lambda self: self.env['account.journal'].search([('type', '=', 'general')],
                                                                                         limit=1))


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_create_bank_move(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        date = self.date_start or self.date_end
        currency = self.company_id.currency_id or self.journal_id.company_id.currency_id
        # amount = currency.round(slip.credit_note and -line.total or line.total)
        # if currency.is_zero(amount):
        #     continue
        res = {
            "journal_id": self.journal_id.id,
            "partner_id": False,
            "date": date,
            'narration': "Règlement bancaire",
            "line_ids": [
                (0, 0, {
                    'account_id': self.company_id.account_salary_id.id,
                    'partner_id': False,
                    'name': self.company_id.account_salary_id.name,
                    'journal_id': self.journal_id.id,
                    'debit': self.amount_total,
                    'credit': 0,
                    'date': date,
                }
                 )
            ]
        }
        if self.dispatched_ids:
            for d in self.dispatched_ids:
                val = {
                    'account_id': d.bank_id.account_id.id,
                    'name': "CAA-LCE (%s)" % d.bank_id.name,
                    'partner_id': False,
                    'debit': 0,
                    'credit': d.amount,
                    'journal_id': self.journal_id.id,
                }
                res['line_ids'].append((0, 0, val))
        move = self.env["account.move"].create(res)
        if move:
            return move.id
        return False

    def generate_move_payslip(self):
        move_ids = []
        templates = self.env["account.move_template"].search([])

        if templates:
            for template in templates.sorted(key=lambda seq: seq.sequence):
                move_val = {
                    'journal_id': template.journal_id.id,
                    'date': self.date_end,
                    'narration': template.name,
                    'ref': self.name,
                    'sequence': template.sequence,
                    'line_ids': []
                }
                ajust = {
                    'name': "Ajustement paie",
                    'journal_id': self.journal_id.id,
                    'debit': 0.0,
                    'credit': 0.0
                }
                debit = credit = 0
                for line in template.line_ids:
                    move_line = {
                        'account_id': line.account_id.id,
                        'name': line.name,
                        'journal_id': self.journal_id.id,
                        'debit': 0.0,
                        'credit': 0.0
                    }
                    line_slips = self.env['hr.payslip.line'].search([('salary_rule_id', 'in', line.rule_ids.ids),
                                                                     ('slip_id', 'in', self.slip_ids.ids)])
                    if line_slips:
                        amount = sum([x.total for x in line_slips])
                        if line.type == 'debit':
                            debit += amount
                            move_line['debit'] = amount
                        else:
                            credit += amount
                            move_line['credit'] = amount
                    if move_line['credit'] != 0.0 or move_line['debit'] != 0.0:
                        move_val['line_ids'].append((0, 0, move_line))

                balance = debit - credit
                if balance > 0.0:
                    ajust['credit'] = balance
                    ajust['account_id'] = self.journal_id.default_credit_account_id.id
                if balance < 0.0:
                    ajust['debit'] = abs(balance)
                    ajust['account_id'] = self.journal_id.default_debit_account_id.id
                if ajust['credit'] != 0.0 or ajust['debit'] != 0.0:
                    move_val['line_ids'].append((0, 0, ajust))
                move = self.env["account.move"].create(move_val)
                if move:
                    move_ids.append(move.id)
        return move_ids
