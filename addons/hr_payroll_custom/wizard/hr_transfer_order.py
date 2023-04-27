# -*- coding:utf-8 -*-

import logging
from odoo import api, fields, models, _
from itertools import groupby
from odoo.tools import format_amount
from odoo.tools import number_to_letter
from math import ceil

_logger = logging.getLogger(__name__)


class HrTransferOrder(models.Model):
    _name = "hr.tansfer.order"
    _description = "transfer order manager"

    @api.depends('order_line_ids')
    def _get_total_amount(self):
        total = sum([x.amount for x in self.order_line_ids])
        self.total = total

    name = fields.Char("Libellé", required=True)
    date_from = fields.Date("Date début", required=True)
    date_to = fields.Date("Date fin", required=True)
    company_id = fields.Many2one('res.company', 'Société', default=lambda self: self.env.user.company_id.id)
    order_line_ids = fields.One2many('hr.transfer.order_line', 'transfer_order_id', 'lignes')
    order_comment_ids = fields.One2many('hr.transfer.order.comment', 'transfer_order_id', 'Commentaires')
    total = fields.Integer('Total général', compute="_get_total_amount", store=True)
    groupby_bank = fields.Boolean("Grouper par banques", default=False)

    def compute(self):
        context = self._context
        datas = {'ids': self.id}
        datas['model'] = self._name
        self.order_line_ids.unlink()
        self.order_comment_ids.unlink()
        payslips = self.env['hr.payslip'].search([('company_id', '=', self.company_id.id),
                                                  ('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to),
                                                  ('state', '=', 'done')])
        res = []
        comment_res = []
        if payslips:
            for slip in payslips:
                amount_order = 0
                slip_amount = slip.get_amount_rubrique('NET')
                if slip.employee_id.dispatch_bank_ids:
                    for x in slip.employee_id.dispatch_bank_ids.sorted(key=lambda seq: seq.sequence):
                        if x.type == 'fix':
                            amount_order += x.amount
                        if x.type == 'perc':
                            amount_order += slip_amount * x.amount / 100
                    if amount_order <= slip_amount:
                        balance = ceil(slip_amount - amount_order)
                        for d_bank in slip.employee_id.dispatch_bank_ids:

                            val = {
                                'employee_id': slip.employee_id.id,
                                'bank_id': d_bank.bank_id.bank_id.id,
                                'acc_bank_id': d_bank.bank_id.id,
                                'amount': d_bank.amount
                            }
                            if d_bank.type == 'balance':
                                val['amount'] = balance
                            if d_bank.type == 'perc':
                                val['amount'] = slip_amount * d_bank.amount / 100
                            res.append(val)
                    else:
                        for rec_bank in slip.employee_id.dispatch_bank_ids.sorted(key=lambda seq: seq.sequence):
                            if 0 < rec_bank.amount <= slip_amount:
                                val = {
                                    'employee_id': slip.employee_id.id,
                                    'bank_id': rec_bank.bank_id.bank_id.id,
                                    'acc_bank_id': rec_bank.bank_id.id,
                                    'amount': rec_bank.amount
                                }
                                res.append(val)
                                slip_amount -= val['amount']
                            elif 0 < slip_amount < rec_bank.amount:

                                val = {
                                    'employee_id': slip.employee_id.id,
                                    'bank_id': rec_bank.bank_id.bank_id.id,
                                    'acc_bank_id': rec_bank.bank_id.id,
                                    'amount': slip_amount
                                }
                                res.append(val)
                                c_vals = {
                                    'employee_id': slip.employee_id.id,
                                    'comment': "Il a été viré " + str(slip_amount) + " FCFA au lieu de " + str(
                                        rec_bank.amount) + " FCFA sur le compte " + str(
                                        rec_bank.bank_id.acc_number) + " domicilié à la banque " + str(
                                        rec_bank.bank_id.bank_id.name)
                                }
                                slip_amount = 0
                                comment_res.append(c_vals)
                            else:
                                pass
                else:
                    val = {
                        'employee_id': slip.employee_id.id,
                        'acc_bank_id': slip.employee_id.main_bank_id.id,
                        'bank_id': slip.employee_id.main_bank_id.bank_id.id,
                        'amount': slip_amount
                    }
                    res.append(val)
        self.order_line_ids = self.order_line_ids.create(res)
        self.order_comment_ids = self.order_comment_ids.create(comment_res)


    def bank_group_line(self):
        """
        Returns this order lines classified by sale_layout_category and separated in
        pages according to the category pagebreaks. Used to render the report.
        """
        self.ensure_one()
        report_pages = [[]]
        for bank, lines in groupby(self.order_line_ids, lambda l: l.bank_id):
            if report_pages[-1] and report_pages[-1][-1]['pagebreak']:
                report_pages.append([])

            val = {
                'name': bank and bank.name or _('Uncategorized'),
                'pagebreak': '',
                'lines': list(lines),
            }
            report_pages[-1].append(val)
        return report_pages

    def sort_bank_group_line(self):
        # A revoir
        res = []
        for page in self.bank_group_line():
            for bank_category in page:
                vals = sorted(bank_category['lines'], key=lambda name: name.employee_id.identification_id)
                res.append(vals)
        print('L108 ', res)
        return res

    def format_amount(self, amount):
        return amount

    def number_to_letter(self, number):
        letter = ''
        if number and isinstance(number, int):
            letter = number_to_letter.number_to_letter_conversion(number)
        return letter


class HrTransferOrderLine(models.Model):
    _name = 'hr.transfer.order_line'
    _description = "order line managment"
    _order = "bank_id"

    num_order = fields.Integer("N° ordre")
    employee_id = fields.Many2one('hr.employee', 'Employé', required=True)
    # acc_bank_id = fields.Char('Compte bancaire', required=False)
    acc_bank_id = fields.Many2one('res.partner.bank', 'Compte bancaire', required=False)
    bank_id = fields.Many2one('res.bank', "Banque", required=False)
    amount = fields.Integer("Salaire")
    transfer_order_id = fields.Many2one('hr.tansfer.order', 'Ordre de transfert', required=False)


class HrTransferOrderComment(models.Model):
    _name = "hr.transfer.order.comment"
    _description = "Transfer Comment Manager"

    employee_id = fields.Many2one("hr.employee", "Employé", required=True)
    comment = fields.Char("Commentaire")
    transfer_order_id = fields.Many2one('hr.tansfer.order', 'Ordre de transfert', required=False)
