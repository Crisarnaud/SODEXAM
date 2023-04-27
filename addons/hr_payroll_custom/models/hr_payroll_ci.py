# -*- encoding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2014 Veone - support.veone.net
# Author: Veone
#
# Fichier du module hr_payroll_ci
# ##############################################################################  -->
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
    _order = 'registration_number, number'

    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    holiday_id = fields.Many2one('hr.leave', string='Congé annuel')
    identification_id = fields.Char(related="employee_id.identification_id", string="Matricule")


    def action_compute_slip_done(self):
        res = {}
        compter = 0
        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date_from or slip.date_to
            name = _('Payslip of %s') % slip.employee_id.name

            """confirmation du bulletin"""
            slip.write({'state': 'done'})
            slip.set_personnal_data()
            compter += 1
        return True

    def action_refresh_from_work_entries(self):
        self.ensure_one()
        self.compute_sheet()

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res = []
        for contract in contracts:
            employee = contract.employee_id
            if employee:
                worked_days = employee.getWorkedDays(date_from, date_to, contract)
                if worked_days:
                    res.append(worked_days)
                else:
                    pass
                overtimes_days = employee.getWorkInput(contract, date_from, date_to)
                if overtimes_days:
                    res += overtimes_days
                else:
                    pass
        return res

    def get_worked_days(self, contracts, date_from, date_to):
        res = []
        for contract in contracts:
            worked_days = contract.employee_id.getWorkedDays(date_from, date_to, contract)
            res += worked_days
            overtimes_days = contract.employee_id.getWorkInput(contract, date_from, date_to)
            res += overtimes_days
        return res

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []
        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

        for contract in contracts:
            inputs = contract.employee_id.getInputsPayroll(contract, date_from, date_to)
            res += inputs
        return res

    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False):
        # defaults
        res = {
            'value': {
                'line_ids': [],
                # delete old input lines
                'input_line_ids': [(2, x,) for x in self.input_line_ids.ids],
                # delete old worked days lines
                'worked_days_line_ids': [(2, x,) for x in self.worked_days_line_ids.ids],
                # 'details_by_salary_head':[], TODO put me back
                'name': '',
                'contract_id': False,
                'struct_id': False,
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        employee = self.env['hr.employee'].browse(employee_id)
        locale = self.env.context.get('lang') or 'en_US'
        res['value'].update({
            'name': _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),
            'company_id': employee.company_id.id,
        })

        if not self.env.context.get('contract'):
            # fill with the first contract of the employee
            contract_ids = self.get_contract(employee, date_from, date_to)
        else:
            if contract_id:
                # set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                # if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(employee, date_from, date_to)

        if not contract_ids:
            return res
        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })
        struct = contract.struct_id
        if not struct:
            return res
        res['value'].update({
            'struct_id': struct.id,
        })
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        res['value'].update({
            'worked_days_line_ids': worked_days_line_ids,
            'input_line_ids': input_line_ids,
        })
        return res

    def compute_dispatched_salary(self):
        for slip in self:
            slip.salary_dispatched_ids.unlink()
            bank_ids = slip.employee_id.dispatch_bank_ids
            amount = slip.get_amount_rubrique('NET')
            lines = []
            if bank_ids:
                lines = slip._compute_dispatched_salary(bank_ids, amount)

            else:
                default_bank = self.env['res.bank'].search([('is_main', '=', True)])
                if default_bank:
                    val = {
                        'bank_id': default_bank.id,
                        'slip_id': slip.id,
                        'amount': amount
                    }
                    lines.append(val)
            if lines:
                slip.salary_dispatched_ids = lines

    def get_days_periode(self, start, end):
        r = (end + timedelta(days=1) - start).days
        return [start + timedelta(days=i) for i in range(r)]

    def write(self, vals):
        emp_obj = self.env['hr.employee']
        trouver = False
        for payslip in self:
            employee = payslip.employee_id
            list_payslips = employee.slip_ids
            date_from = fields.Datetime.from_string(payslip.date_from)
            date_to = fields.Datetime.from_string(payslip.date_to)
            Range = namedtuple('Range', ['start', 'end'])
            r1 = Range(start=date_from, end=date_to)
            new_list = []
            if (len(list_payslips) != 1):
                for slip in list_payslips:
                    if slip.id != payslip.id:
                        new_list.append(slip)
                for slip in new_list:
                    old_date_from = fields.Datetime.from_string(slip.date_from)
                    old_date_to = fields.Datetime.from_string(slip.date_to)
                    r2 = Range(start=old_date_from, end=old_date_to)
                    result = (min(r1.end, r2.end) - max(r1.start, r2.start)).days + 1
            if trouver == True:
                raise ValidationError(_("L'employé possède déjà un bulletin pour cette période"))
            else:
                super(HrPayslip, self).write(vals)
        return True

    def _get_inputs_lines(self):
        res = []
        contract_ids = []
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = self.get_contract(employee, date_from, date_to)
        contracts = self.env['hr.contract'].browse(contract_ids)
        for contract in contracts:
            inputs = self.get_inputs(contract, date_from, date_to)
            if inputs:
                res += inputs
        return res

    def _get_new_worked_days_lines(self):
        """
        Calcul des jours travaillés sur le bulletin de salaire
        :return:
        """
        super()._get_new_worked_days_lines()
        res = []
        contract_ids = []
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = self.get_contract(employee, date_from, date_to)
        contracts = self.env['hr.contract'].browse(contract_ids)

        leave_paid = self.env['hr.leave'].search(
            [('state', '=', 'validate'), ('to_pay', '=', False), ('payslip_status', '=', True),
             ('employee_id', '=', self.employee_id.id)], limit=1)
        for contract in contracts:
            employee = contract.employee_id
            if employee:
                if leave_paid:
                    entry = self.env['hr.work.entry.type'].search([('code', '=', 'WORK100')])
                    salary_rule = self.env['hr.salary.rule'].search([('code', '=', 'WORK100')], limit=1)

                    if leave_paid.request_date_to.month == self.date_from.month and leave_paid.request_date_to.month != self.date_from.month:
                        attendances = {
                            'name': _("Normal Working Days paid at 100%"),
                            'sequence': 1,
                            'code': 'WORK100',
                            'number_of_days': 30 - leave_paid.date_to.day,
                            'number_of_hours': 173.33 * (30 - leave_paid.date_to.day) / 30,
                            'contract_id': contract.id,
                            'work_entry_type_id': entry.id,
                            'salary_rule_id': salary_rule.id
                        }
                        res.append(attendances)
                    if leave_paid.request_date_to.month == self.date_from.month and leave_paid.request_date_from.month == self.date_from.month:
                        attendances = {
                            'name': _("Normal Working Days paid at 100%"),
                            'sequence': 1,
                            'code': 'WORK100',
                            'number_of_days': (self.date_to.day - leave_paid.date_to.day) + (leave_paid.date_from.day - 1),
                            'number_of_hours': 173.33 * (self.date_to.day - leave_paid.number_of_days) / 30,
                            'contract_id': contract.id,
                            'work_entry_type_id': entry.id,
                            'salary_rule_id': salary_rule.id
                        }
                        res.append(attendances)
                    else:
                        attendances = {
                            'name': _("Normal Working Days paid at 100%"),
                            'sequence': 1,
                            'code': 'WORK100',
                            'number_of_days': 30,
                            'number_of_hours': 173.33,
                            'contract_id': contract.id,
                            'work_entry_type_id': entry.id,
                            'salary_rule_id': salary_rule.id
                        }
                        res.append(attendances)
                else:
                    worked_days = self.employee_id.getWorkedDays(date_from, date_to, contract)
                    if worked_days:
                        res += worked_days
                    else:
                        pass

            overtimes_days = employee.getWorkInput(contract, date_from, date_to)
            if overtimes_days:
                res += overtimes_days
            else:
                pass

        return res

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []

        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

            if not self.contract_id.struct_id:
                return
            self.struct_id = self.contract_id.struct_id

        self.company_id = employee.company_id
        if not self.contract_id or self.employee_id != self.contract_id.employee_id:  # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id

        lang = employee.sudo().address_home_id.lang or self.env.user.lang
        context = {'lang': lang}
        payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        del context

        self.name = '%s - %s - %s' % (
            payslip_name,
            self.employee_id.name or '',
            format_date(self.env, self.date_from, date_format="MMMM y", lang_code=lang)
        )
        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _(
                "This payslip can be erroneous! Work entries may not be generated for the period from %(start)s to %(end)s.",
                start=date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1),
                end=date_to,
            )
        else:
            worked_days_line_ids = self._get_new_worked_days_lines()
            worked_days_lines = self.worked_days_line_ids.browse([])
            for r in worked_days_line_ids:
                worked_days_lines += worked_days_lines.new(r)
            self.worked_days_line_ids = worked_days_lines
            contracts = self.env['hr.contract'].browse(contract_ids)
            input_line_ids = self._get_inputs_lines()
            input_lines = self.input_line_ids.browse([])
            for r in input_line_ids:
                input_lines += input_lines.new(r)
            self.input_line_ids = input_lines
            self.warning_message = False
        return

    def get_emprunt_montant_monthly(self, employee_id, date_from, date_to):
        ech_obj = self.env['hr.emprunt.loaning.line']
        if employee_id and date_from and date_to:
            lines = ech_obj.search([]).filtered(lambda l: l.loaning_id.employee_id == employee_id and l.statut_echeance
                                                          == False)
            true_line = lines.filtered(lambda t: date_from <= t.date_prevu <= date_to)
            return true_line
        return False

    @api.depends('contract_id')
    def _get_anciennete(self):
        for slip in self:
            end_date = fields.Datetime.from_string(slip.date_to)
            start_date = fields.Datetime.from_string(slip.employee_id.start_date)
            tmp = relativedelta.relativedelta(end_date, start_date)
            slip.update({
                'payslip_an_anciennete': tmp.years,
                'payslip_mois_anciennete': tmp.months,
            })

    def _get_last_payslip(self):
        dic = {}
        res = []
        slips = self.employee_id.slip_ids
        if (len(slips) == 1):
            self.last_payslip = False
        else:
            for slip in slips:
                if slip.id < self.id:
                    res.append(slip)
                    if len(res) >= 1:
                        dernier = res[len(res) - 1]
                        payslip = self.self.env['hr.payslip'].search([('id', '=', dernier.id)])
                        self.last_payslip = payslip.id

    def _get_total_gain(self):
        res = {}
        for line in self.line_ids:
            if line.code == 'BRUT':
                self.total_gain = line.total
        return res

    def _get_retenues(self):
        for line in self.line_ids:
            if line.code == 'RET':
                self.total_retenues = line.total

    @api.depends('line_ids.total')
    def _get_net_paye(self):
        for slip in self:
            for line in slip.line_ids:
                if line.code == "NET":
                    slip.update({
                        'net_paie': line.total,
                    })

    def get_amountbycode(self, code, line_ids):
        amount = 0
        if line_ids:
            for line in line_ids:
                if line.code == code:
                    return line.total
        return 0

    def getDatabyCode(self, code, line_ids, field_name):
        amount = 0
        if line_ids and field_name in ('rate', 'amount', 'quantity'):
            for line in line_ids:
                if line.code == code:
                    if field_name == 'rate':
                        return line.rate
                    if field_name == 'amount':
                        return line.amount
                    if field_name == 'quantity':
                        return line.quantity
        return amount

    def cumulBYCode(self, employee_id, code, date_from, date_to):
        slip_obj = self.env['hr.payslip']
        payslips = slip_obj.search([('date_from', '>=', date_from), ('date_to', '<=', date_to),
                                    ('employee_id', '=', employee_id)])
        total_amount = 0
        for slip in payslips:
            result = slip.get_amountbycode(code, slip.line_ids)
            total_amount += result
        return total_amount

    def getCumulDataByCode(self, employee_id, code, date_from, date_to, field_name):
        payslips = self.env['hr.payslip'].search([('date_from', '>=', date_from), ('date_to', '<=', date_to),
                                                  ('employee_id', '=', employee_id)])
        cumul_amount = 0
        for payslip in payslips:
            result = payslip.getDatabyCode(code, payslip.line_ids, field_name)
            cumul_amount += result
        return cumul_amount

    def get_cumul_base_impot(self):
        year = datetime.now().year
        date_temp = fields.Datetime.from_string(self.date_from)
        first_day = str(date_temp + relativedelta.relativedelta(month=1, day=1))[:10]

        for payslip in self:
            total = payslip.cumulBYCode(payslip.employee_id.id, 'SNI', first_day, payslip.date_from)
            date_to = fields.Datetime.from_string(payslip.date_to)
            payslip.update({
                'cumul_base_impot': payslip.cumulBYCode(payslip.employee_id.id, 'BASE_IMP', first_day,
                                                        payslip.date_from),
                'cumul_cn': payslip.cumulBYCode(payslip.employee_id.id, 'CN', first_day, payslip.date_from),
                'cumul_worked_days': payslip.cumulBYCode(payslip.employee_id.id, 'TJRPAY', first_day,
                                                         payslip.date_from),
                'cumul_igr': payslip.cumulBYCode(payslip.employee_id.id, 'IGR', first_day, payslip.date_from),
                'number_of_month': date_to.month,
                'worked_days': payslip.cumulBYCode(payslip.employee_id.id, 'CON', first_day, payslip.date_from),
                'cumul_brut_percu': payslip.cumulBYCode(payslip.employee_id.id, 'BRUT', first_day,
                                                        payslip.date_from),
                'cumul_is_paid': payslip.cumulBYCode(payslip.employee_id.id, 'ITS', first_day, payslip.date_from),
                'cumul_igr_paid': payslip.cumulBYCode(payslip.employee_id.id, 'IGR', first_day, payslip.date_from),
                'cumul_cn_paid': payslip.cumulBYCode(payslip.employee_id.id, 'CN', first_day, payslip.date_from),
                'cumul_salary_charges': payslip.cumulBYCode(payslip.employee_id.id, 'RET', first_day,
                                                            payslip.date_from),
                'cumul_employer_charges': payslip.cumulBYCode(payslip.employee_id.id, 'TCP_A', first_day,
                                                              payslip.date_from),
                'cumul_salary_charges_cnps': payslip.cumulBYCode(payslip.employee_id.id, 'RET', first_day,
                                                                 payslip.date_from),
                'cumul_employer_charges_cnps': payslip.cumulBYCode(payslip.employee_id.id, 'TCP_A_CNPS', first_day,
                                                                   payslip.date_from),
                'cumul_cnps_paid': payslip.cumulBYCode(payslip.employee_id.id, 'CNPS', first_day, payslip.date_from),
                'cumul_cgrae_paid': payslip.cumulBYCode(payslip.employee_id.id, 'CGRAE_E', first_day,
                                                        payslip.date_from),
                'cumul_cmu_paid': payslip.cumulBYCode(payslip.employee_id.id, 'CMU', first_day, payslip.date_from),
                'cumul_crrae_employee_paid': payslip.cumulBYCode(payslip.employee_id.id, 'CRRAE_E', first_day,
                                                                 payslip.date_from) + payslip.cumulBYCode(
                    payslip.employee_id.id, 'REG_CRRAE_E', first_day, payslip.date_from),
                'cumul_crrae_faam_employee_paid': payslip.cumulBYCode(payslip.employee_id.id, 'C_FAAM_E', first_day,
                                                                      payslip.date_from) + payslip.cumulBYCode(
                    payslip.employee_id.id, 'REG_C_FAAM_E', first_day, payslip.date_from)
            })

    def get_somme_rubrique(self, code):
        annee = self.date_to.year
        for payslip in self:
            cpt = 0
            for line in self.line_ids:
                if line.salary_rule_id.code == code and self.date_to >= self.date_to and payslip.date_to.year == annee:
                    cpt += line.total
            result = cpt
            return result

    def get_amount_rubrique(self, rubrique):
        line_ids = self.line_ids
        total = 0
        for line in line_ids:
            if line.code == rubrique:
                total = line.total
        return total

    def getTauxByCode(self, rubrique):
        taux = 0.0
        lines = self.line_ids
        for line in lines:
            if line.code == rubrique:
                taux = line.rate
        return taux

    def getLineByCode(self, code):
        lines = self.line_ids
        for line in lines:
            if line.code == code:
                return line

    def _get_total(self):
        self.worked_days = 0.0

    @api.depends("line_ids")
    def _get_basic_element(self):
        for slip in self:
            base_daily = slip.line_ids.filtered(lambda l: l.code == 'BASE_J')
            brut_imposable = slip.line_ids.filtered(lambda l: l.code == 'BRUT')
            brut_total = slip.line_ids.filtered(lambda l: l.code == 'BRUT_TOTAL')
            if base_daily:
                slip.base_daily = base_daily.total
            if brut_imposable:
                slip.brut_imposable = brut_imposable.total
            if brut_total:
                slip.brut_total = brut_total.total

    def action_payslip_cancel(self):
        moves = self.mapped('move_id')
        moves.filtered(lambda x: x.state == 'posted')
        moves.unlink()
        return super(HrPayslip, self).action_payslip_cancel()

    def set_personnal_data(self):
        self.write(
            {'igr_part': self.employee_id.part_igr,
             'marital_status': self.employee_id.marital,
             })

    def get_brut_amount(self):
        brut_amount = 0
        for line in self.line_ids:
            if line.code == 'BRUT':
                brut_amount = line.total
        return brut_amount

    registration_number = fields.Char('Matricule ', related='employee_id.identification_id', store=True)
    option_salaire = fields.Selection([('mois', 'Mensuel'), ('jour', 'Journalier'), ('heure', 'horaire')],
                                      string='Option salaire', index=True, readonly=False)
    reference_reglement = fields.Char('Reférence', size=60, required=False)
    payslip_an_anciennete = fields.Integer("Nombre d'année", compute=_get_anciennete)
    payslip_mois_anciennete = fields.Integer("Nombre de mois (Ancienneté)", compute=_get_anciennete)
    payment_method = fields.Selection([('espece', 'Espèces'), ('virement', 'Virement bancaire'), ('cheque', 'Chèques')],
                                      string='Moyens de paiement', required=False, default='espece')
    last_payslip = fields.Many2one("hr.payslip", compute=_get_last_payslip, store=True, string="Dernier bulletin")
    total_gain = fields.Integer(compute=_get_total_gain, store=True)
    total_retenues = fields.Integer(compute=_get_retenues, store=True)
    net_paie = fields.Integer(compute=_get_net_paye, store=True)
    cumul_base_impot = fields.Float('Cumul base impôt')
    cumul_cn = fields.Float('Cumul CN')
    cumul_is = fields.Float('Cumul IS')
    cumul_igr = fields.Float('Cumul IGR')
    cumul_worked_days = fields.Float('Cumul jours travaillés', compute=get_cumul_base_impot)
    worked_days = fields.Float('Total jours travaillés', compute=get_cumul_base_impot)
    contribution_days = fields.Integer("Nombre de jours fiscaux", default=30)
    number_of_month = fields.Integer('Nombre de mois', compute='get_cumul_base_impot')
    type = fields.Selection([('h', 'Horaire'), ('j', 'Journalier'), ('m', 'Mensuel')], 'Type',
                            related="employee_id.type")
    igr_part = fields.Float('IGR')
    marital_status = fields.Selection([
        ('single', 'Célibataire'),
        ('married', 'Marié(e)'),
        ('cohabitant', 'Cohabitant légal'),
        ('widower', 'Veuf(ve)'),
        ('divorced', 'Divorcé(e)')], string='Marital Status')
    department_id = fields.Many2one('hr.department', 'Departement', related="employee_id.department_id")
    nature_employe = fields.Selection([('local', 'Local'), ('expat', 'Expatrié')], "Nature de l'employé",
                                      related='employee_id.nature_employe')
    base_daily = fields.Float("Base journalière", compute="_get_basic_element", store=True)
    brut_imposable = fields.Float("Brut imposable", compute="_get_basic_element", store=True)
    brut_total = fields.Float("Brut Total", compute="_get_basic_element", store=True)
    include_gratification = fields.Boolean("Inclure la gratification", default=False)
    cumul_brut_percu = fields.Float("Cumul Brut perçu", compute=get_cumul_base_impot)
    cumul_periode_travaille = fields.Float("Cumul période travailléé")
    cumul_is_paid = fields.Float('Cumul IS payé', compute=get_cumul_base_impot)
    cumul_igr_paid = fields.Float('Cumul IGR payé', compute=get_cumul_base_impot)
    cumul_cn_paid = fields.Float('Cumul CN payé', compute=get_cumul_base_impot)
    cumul_salary_charges = fields.Float('Cumul Charges Salariales', compute=get_cumul_base_impot)
    cumul_employer_charges = fields.Float('Cumul Charges Patronales', compute=get_cumul_base_impot)
    cumul_salary_charges_cnps = fields.Float('Cumul Charges Salariales CNPS', compute=get_cumul_base_impot)
    cumul_employer_charges_cnps = fields.Float('Cumul Charges Patronales CNPS', compute=get_cumul_base_impot)
    cumul_cnps_paid = fields.Float('Cumul CNPS payé', compute=get_cumul_base_impot)
    cumul_cgrae_paid = fields.Float('Cumul CGRAE payé', compute=get_cumul_base_impot)
    cumul_cmu_paid = fields.Float('Cumul CMU payé', compute=get_cumul_base_impot)
    cumul_crrae_employee_paid = fields.Float('Cumul CRRAE Employé', compute=get_cumul_base_impot)
    cumul_crrae_faam_employee_paid = fields.Float('Cumul CRRAE FAAM Employé', compute=get_cumul_base_impot)
    acquired_leave_month = fields.Float('Congés acquis mensuel')
    taked_leave_month = fields.Float('Congés pris mensuel')
    acquired_leave = fields.Float('Congés acquis')
    taked_leave = fields.Float('Congés pris')
    available_leave = fields.Float('Congés disponible')
    days_since_last_leave = fields.Integer('Jours depuis dernier congé', compute='get_cumul_holiday')
    gross_salary_leave = fields.Integer('Brut congé', compute='get_cumul_holiday')
    number_days_off = fields.Integer('Nombre de jour de congé', compute='get_number_days_off', store=True)
    number_remaining_days_leave = fields.Integer('Nombre de jour de reliquat congé',
                                                 compute='get_number_days_off', store=True)
    input_line_ids = fields.One2many(compute='_onchange_employee', store=True)
    salary_dispatched_ids = fields.One2many('hr.payroll.salary_dispatched', 'slip_id',
                                            'Distribution du salaire sur les comptes', required=False)

    worked_days_line_ids = fields.One2many('hr.payslip.worked_days', 'payslip_id', store=True,
                                           string='Payslip Worked Days', copy=True, readonly=False,
                                           states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})

    @api.onchange('include_gratification', 'input_line_ids')
    def action_include_gratification(self):
        if self.include_gratification and self.input_line_ids:
            self.update({
                'input_line_ids': [],
            })

    def get_list_employee(self):
        hc_obj = self.env['hr.contract']
        hcontract_ids = hc_obj.search([('state', '=', 'in_progress')])
        self.env.cr.execute("SELECT employee_id FROM hr_contract WHERE id=ANY(%s)", (hcontract_ids,))
        results = self.env.cr.fetchall()
        if results:
            list_employees = [res[0] for res in results]
            return {'domain': {'employee_id': [('id', 'in', list_employees)]}}

    def get_net_paye(self):
        montant = 0
        for line in self.line_ids:
            if line.code == "NET":
                montant = line.total
        return montant

    def get_cumul_holiday(self):
        """
        determiner  le nombre de jours travaillé depuis dernier congé
        """
        date_temp = fields.Datetime.from_string(self.date_from)
        first_day = str(date_temp + relativedelta.relativedelta(month=1, day=1))[:10]
        date_payment_last_holiday = self.employee_id.annual_leave_payment_date or \
                                    (datetime.strptime(first_day, "%Y-%m-%d")).date()
        self.days_since_last_leave = self.cumulBYCode(self.employee_id.id, 'WORK100', date_payment_last_holiday,
                                                      self.date_to)

        """
        Faire le cumul des bruts depuis dernier congé
        """
        gross_month = self.get_amountbycode('BRUT', self.line_ids)
        if str(date_payment_last_holiday) < first_day:
            self.gross_salary_leave = self.cumulBYCode(self.employee_id.id, 'BRUT', first_day,
                                                       self.date_from) + gross_month + self.employee_id.leave_balance
        else:
            self.gross_salary_leave = self.cumulBYCode(self.employee_id.id, 'BRUT', date_payment_last_holiday,
                                                       self.date_to)

    def compute_leave_amount(self, id_employee):
        """
        Function calculating the amount of paid leaves according to the "last 12 months" method
        :param id_employee:
        :return: amount
        """
        # 1- determiner la periode de reference
        employee_rc = self.env['hr.employee'].search([('id', '=', id_employee)], limit=1)
        system_implementation_date = employee_rc.company_id.system_implementation_date
        last_leave_payment_date = employee_rc.payment_date_last_holiday

        hiring_date = employee_rc.start_date
        gross_previous_leave = employee_rc.brut_holiday
        begin_date = []
        if not system_implementation_date:
            raise Warning(_("La date de mise en service de l'application doit être définie dans les paramètres de "
                            "la société"))
        if last_leave_payment_date:
            if last_leave_payment_date < system_implementation_date:
                date_begin = last_leave_payment_date
                gross_previous_leave = employee_rc.brut_holiday
                begin_date.append(date_begin)
            else:
                date_begin = last_leave_payment_date
                begin_date.append(date_begin)

        elif hiring_date and hiring_date < system_implementation_date:
            date_begin = hiring_date
            gross_previous_leave = employee_rc.brut_holiday
            begin_date.append(date_begin)

        elif hiring_date and hiring_date >= system_implementation_date:
            date_begin = hiring_date
            begin_date.append(date_begin)

        else:
            pass

        today = self.date_to
        date_begin = begin_date[0]
        if date_begin:
            reference_months = relativedelta.relativedelta(today, date_begin) if today > date_begin \
                else relativedelta.relativedelta(date_begin, today)
        else:
            raise Warning(_("Une erreur a été rencontrée. Merci de vérifier que la date de payement du dernier congé ou"
                            " la date d'embauche a été définie"))
        rate_employee = employee_rc.company_id.number_holidays_expat if employee_rc.nature_employe == 'expat' \
            else employee_rc.company_id.number_holidays_locaux

        # 2- rechercher les règles faisant partie du calcul de l'allocation congés-payés
        payslip = self.env['hr.payslip'].search([('state', '=', 'done')])
        rules = self.env['hr.salary.rule'].search([('use_to_compute_leave', '=', True)])

        # 3- recuperer pour chaque bulletin les éléments faisant partie du calcul (salaire de base, sursalaire...)
        # et faire le cumul
        cumulative_wages = 0
        if rules:
            for rule in rules:
                cumulative_wages += payslip.cumulBYCode(id_employee, rule.code, date_begin, today)
        else:
            raise Warning(_("Aucune regle n'a été definie pour le calcul de l'allocation congés payés"))

        # 4- Ajouter brut congé antérieur et calculer le salaire moyen
        cumulative_wages += gross_previous_leave

        ref_months = ceil(reference_months.months + reference_months.years * 12 + reference_months.days / 30)
        average_wage = cumulative_wages / (ref_months if ref_months > 0 else 1)

        # 5- Calculer le salaire journalier
        daily_salary = average_wage / 30

        # 6- Calculer le montant de l'allocation en fonction du nombre de jour de congé
        leaves = self.env['hr.leave'].search(
            [('state', '=', 'validate'), ('to_pay', '=', True), ('payslip_status', '=', False),
             ('holiday_status_id.code', '=', 'CONG'),
             ('employee_id', '=', id_employee)], limit=1)

        number_days_off = employee_rc.leaves_count
        _logger.info('hhhhhhhhhhh %s', number_days_off)
        number_days_off_legal = leaves.number_of_days
        date_start = leaves.date_from
        date_end = leaves.date_to
        date_return = leaves.request_date_to
        taken_into_account = leaves.to_pay

        if leaves:
            leave_allowance = ceil(daily_salary * number_days_off * 1.25)
        else:
            leave_allowance = 0

        # 7- retourner la valeur calculée
        return leave_allowance, number_days_off, date_start, date_end, date_return, taken_into_account, number_days_off_legal

    def calculate_leave_allowances(self):
        for rec in self:
            # 1- rechercher à partir du code congé, l'enregistrement congé annuel ou congé payé dans autres entrées
            other_entries = self.env['hr.payslip.input'].search([('code', 'in', ('CONG', 'CNGP')),
                                                                 ('payslip_id', '=', rec.id)])

            # 2- Si trouvé, mettre à jour le montant. Si non, créer la ligne avec comme montant, celle que nous avons calculée

            if len(other_entries) > 1:
                for element in other_entries:
                    element.unlink()
                other_entries = self.env['hr.payslip.input'].search([('code', 'in', ('CONG', 'CNGP')),
                                                                     ('payslip_id', '=', rec.id)])
            if len(other_entries) == 1:
                other_entries.amount = rec.compute_leave_amount(self.employee_id.id)[0]
                other_entries.number_days_off = rec.compute_leave_amount(self.employee_id.id)[0]

            if not other_entries:
                leaves = self.env['hr.leave'].search(
                    [('state', '=', 'validate'), ('to_pay', '=', True), ('payslip_status', '=', False),
                     ('holiday_status_id.code', '=', 'CONG'),
                     ('employee_id', '=', rec.employee_id.id)],
                    limit=1)
                salary_rule = self.env['hr.salary.rule'].search([('code', '=', 'CONG')], limit=1)
                if rec.compute_leave_amount(self.employee_id.id)[0] != 0:
                    vals = {
                        'contract_id': rec.contract_id.id,
                        'payslip_id': rec.id,
                        'name': salary_rule.name,
                        'salary_rule_id': salary_rule.id,
                        'number_days_off': leaves.number_of_days if leaves else '',
                        'amount': rec.compute_leave_amount(self.employee_id.id)[0],
                        'code': salary_rule.code
                    }
                    self.env['hr.payslip.input'].create(vals)

            # 3- Rechercher dans les jours travaillés, le work100 et réinitialiser le nombre de jour et d'heures
            works_days = self.env['hr.payslip.worked_days'].search([('code', '=', 'WORK100'),
                                                                    ('payslip_id', '=', rec.id)], limit=1)
            start_date_leave = rec.compute_leave_amount(self.employee_id.id)[2]
            return_date_leave = rec.compute_leave_amount(self.employee_id.id)[3]

            if rec.compute_leave_amount(self.employee_id.id)[3]:
                if rec.compute_leave_amount(self.employee_id.id)[3].month == self.date_from.month:
                    works_days.number_of_days = 30 - rec.compute_leave_amount(self.employee_id.id)[
                        3].day
                    works_days.number_of_hours = (works_days.number_of_days * 173.33) / 30
                else:
                    if start_date_leave.month == self.date_from.month:
                        works_days.number_of_days = rec.compute_leave_amount(self.employee_id.id)[3].day - 1
                        works_days.number_of_hours = (works_days.number_of_days * 173.33) / 30

                if (start_date_leave.month == self.date_from.month) and (
                        return_date_leave.month == self.date_from.month):
                    works_days.number_of_days = (30 - rec.compute_leave_amount(self.employee_id.id)[6])
                    works_days.number_of_hours = (works_days.number_of_days * 173.33) / 30

            # 4 recuperer le nombre de jour de congé et recalculer le bulletin
            rec.get_number_days_off()
            rec.compute_sheet()

    @api.depends('input_line_ids')
    def get_number_days_off(self):
        for rec in self:
            for line in rec.input_line_ids:
                if line.code in {'CONG', 'CNGP'}:
                    rec.number_days_off = rec.compute_leave_amount(self.employee_id.id)[1]
                if line.code in {'RQ_CONG', 'RQ_CNGP'}:
                    rec.number_remaining_days_leave = line.number_days_off

    def compute_sheet(self):
        result = super(HrPayslip, self).compute_sheet()
        hpana_obj = self.env['hr.payroll.analyse']

        for slip in self:
            _logger.info("aaaaaaaaaaaaaaaaa %s", slip.employee_id.allocation_count)
            _logger.info("nnnnnnnnnnnnnnnnnn %s", slip.employee_id.remaining_leaves)
            _logger.info("oooooooooooooooooo %s", slip.employee_id.leaves_count)
            hpana_obj.search([('slip_id', '=', slip.id)]).unlink()
            vals = {
                'employee_id': slip.employee_id.id,
                'date': slip.date_from,
                'slip_id': slip.id,
                'base': slip.get_amountbycode('BASE', slip.line_ids),
                'sursalaire': slip.get_amountbycode('SURSA', slip.line_ids),
                'primes': slip.get_amountbycode('TTPRIM', slip.line_ids),
                'brut': slip.get_amountbycode('BRUT', slip.line_ids),
                'retenues': slip.get_amountbycode('RET', slip.line_ids),
                'transport': slip.get_amountbycode('TRSP', slip.line_ids),
                'net_paie': slip.get_amountbycode('NET_PAIE', slip.line_ids),
                'emprunt': slip.get_amountbycode('EMP', slip.line_ids),
                'net': slip.get_amountbycode('NET', slip.line_ids),
            }
            hpana_obj.create(vals)
            slip.employee_id.remaining_leaves = 0
            _logger.info("iiiiiiiiiiiiiiiiiiiiiiiiii %s", slip.employee_id.remaining_leaves)
        return result

    def unlink(self):
        for slip in self:
            self.env['hr.payroll.analyse'].search([('slip_id', '=', slip.id)]).unlink()
        return super(HrPayslip, self).unlink()

    def send_notification(self, email_id, context=None):
        template_id = self.env['ir.model.data'].get_object_reference('hr_payroll_custom', email_id)
        try:
            mail_templ = self.env['mail.template'].browse(template_id[1])
            result = mail_templ.send_mail(res_id=self.id, force_send=True)
            return True
        except:
            return False

    def action_payslip_done(self):
        now = datetime.now()
        for slip in self:
            analyse = self.env['hr.payroll.analyse'].search([('slip_id', '=', slip.id)])
            if analyse:
                analyse.write({'state': 'done'})
                slip.write({'state': 'done'})
                slip.set_personnal_data()
                self.send_notification('email_template_payslip')
            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', slip.employee_id.id), ('state', '=', 'validate'),
                 ('to_pay', '=', True), ('payslip_status', '=', False), ('holiday_status_id.code', '=', 'CONG')], limit=1)
            if leaves:
                leaves.payslip_id = slip.id
                leaves.to_pay = False
                leaves.payslip_status = True
                slip.employee_id.leaves_count = 0
                slip.employee_id.remaining_leaves = 0
                slip.employee_id.allocation_used_display = 0
                slip.employee_id.allocation_display = 0
                return

    def _get_tranche(self):
        type = 'm'
        if self.employee_id.type != 'm':
            tranches = self.env['hr.cnps.setting'].search([('type', '=', 'j')])
            self.env.cr.execute("SELECT amount FROM hr_payslip_line WHERE code = 'BASE' AND slip_id = %s" % (self.id))
            result = self.env.cr.fetchone()
            if tranches:
                for tranche in tranches:
                    if result[0] >= tranche.amount_min and result[0] <= tranche.amount_max:
                        self.tranche_id = tranche.id
        else:
            tranches = self.env['hr.cnps.setting'].search([('type', '=', 'm')])
            self.env.cr.execute("SELECT total FROM hr_payslip_line WHERE code = 'BASE' AND slip_id = %s" % (self.id))
            result = self.env.cr.fetchone()
            if tranches:
                for tranche in tranches:
                    if result[0] >= tranche.amount_min and result[0] <= tranche.amount_max:
                        self.tranche_id = tranche.id

            print(result)

    tranche_id = fields.Many2one('hr.cnps.setting', 'Tranche', store=False)

    def send_mail_payslip(self):
        today = datetime.today()
        config_rc = self.env['res.config.settings'].search([], limit=1)
        slips = self.env['hr.payslip'].search([])
        email_template_id = self.env.ref('hr_payroll_custom.email_template_payslip').id
        email_template = self.env['mail.template'].browse(email_template_id)
        for slip in slips:
            email_template.send_mail(res_id=slip.employee_id.id, force_send=True)


class HrPayslipLine(models.Model):
    """Payslip Line"""

    _name = 'hr.payslip.line'
    _inherit = 'hr.payslip.line'

    def _calculate_total(self):
        if not self: return {}
        res = {}
        for line in self:
            self.total = float(line.quantity) * line.amount * line.rate / 100

    def _get_element(self):
        for line in self:
            line.date_from = line.slip_id.date_from
            line.date_to = line.slip_id.date_to

    def determine_annual_leave_payment_date(self):
        """
        Fonction permettant de déterminer la date de paiement des congés annuels
        :return: null
        """
        if self.salary_rule_id and self.contract_id and self.employee_id:
            if self.total > 0 and (self.salary_rule_id.code == 'CONG' or self.salary_rule_id.code == 'CNGP'):
                employee_rec = self.env['hr.employee'].search([('id', '=', self.employee_id.id)])
                employee_rec.write({'annual_leave_payment_date': self.slip_id.date_to})

    @api.model
    def create(self, vals):
        record = super(HrPayslipLine, self).create(vals)
        record.determine_annual_leave_payment_date()
        return record

    def write(self, vals):
        record = super(HrPayslipLine, self).write(vals)
        self.determine_annual_leave_payment_date()
        return record

    amount = fields.Float('Amount', digits=(16, 0))
    quantity = fields.Float('Quantity', digits=(16, 4))
    rate = fields.Float(string='Rate (%)', digits=(16, 2), default=100)
    total = fields.Float(compute='_compute_total', string='Total', digits=(16, 0), store=True)
    date_from = fields.Date(string='Date From', related='slip_id.date_from', store=True)
    date_to = fields.Date(string='Date To', related='slip_id.date_to', store=True)
    appears_on_payroll = fields.Boolean('Apparaît dans le livre de paie', related='salary_rule_id.appears_on_payroll',
                                        store=True)


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    @api.onchange('number_of_days', 'number_of_hours')
    def onChangeElementWD(self):
        if self.code == 'WORK100':
            self.rate = (self.number_of_days / 30)
            self.number_of_hours = (self.number_of_days * 173.33) / 30

    rate = fields.Float('Taux')
    number_days_off = fields.Integer('Nombre de jour de congé', default=1)
    work_entry_type_id = fields.Many2one('hr.work.entry.type', string='Type',
                                         required=False, store=True,
                                         readonly=False,
                                         help="The code that can be used in the salary rules")
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', readonly=False,
                                 required=False, ondelete='cascade',
                                 index=True, store=True)

    name = fields.Char(related='work_entry_type_id.name', string='Description', readonly=False, store=True)
    sequence = fields.Integer(required=False, index=True, default=10, store=True)
    code = fields.Char(string='Code', related='work_entry_type_id.code', store=True, readonly=False)
    number_of_days = fields.Float(string='Number of Days', store=True, readonly=False)
    number_of_hours = fields.Float(string='Number of Hours', store=True, readonly=False)
    is_paid = fields.Boolean(compute='_compute_is_paid', store=True)
    amount = fields.Monetary(string='Amount', compute='_compute_amount', store=True, readonly=False)
    contract_id = fields.Many2one(related='payslip_id.contract_id', string='Contract', store=True,
                                  help="The contract for which apply this worked days")
    salary_rule_id = fields.Many2one('hr.salary.rule', 'Règle salariale')


class HrPayrollInput(models.Model):
    _inherit = "hr.payslip.input"

    salary_rule_id = fields.Many2one('hr.salary.rule', 'Règle salariale')
    name = fields.Char(related='input_type_id.name', string="Name", readonly=False, store=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=False, store=True, ondelete='cascade',
                                 index=True)
    code = fields.Char(compute='get_salary_rule_code', store=True, readonly=0, required=False)
    number_days_off = fields.Integer('Nombre de jour de congé', compute='compute_number_day_off')
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Description', required=False,
                                    domain="['|', ('id', 'in', _allowed_input_type_ids), ('struct_ids', '=', False)]")

    def compute_number_day_off(self):
        leaves = self.env['hr.leave'].search([('state', '=', 'validate')])
        for leave in leaves:
            if self.payslip_id.employee_id.id == leave.employee_id.id:
                self.number_days_off = leave.number_of_days

    @api.depends('salary_rule_id')
    def get_salary_rule_code(self):
        if self.salary_rule_id and not self.code:
            self.code = self.salary_rule_id.code
            self.name = self.salary_rule_id.name
            self.contract_id = self.payslip_id.contract_id.id
        if self.code and not self.salary_rule_id:
            self.salary_rule_id = self.env['hr.salary.rule'].search([('code', '=', self.code)]).id

    @api.model
    def create(self, vals):
        if 'code' in vals and not 'salary_rule_id' in vals:
            vals['salary_rule_id'] = self.env['hr.salary.rule'].search([('code', '=', vals['code'])]).id
        if 'code' in vals and vals['code'] == 'R_LOG':
            vals['salary_rule_id'] = self.env['hr.salary.rule'].search([('code', '=', 'R_INDML')]).id
        if 'code' in vals and vals['code'] == 'TRSPT_PRES':
            vals['salary_rule_id'] = self.env['hr.salary.rule'].search([('code', '=', 'TRSPT_PERS')]).id
        record = super(HrPayrollInput, self).create(vals)
        return record

    def write(self, vals):
        if 'code' in vals and not 'salary_rule_id' in vals:
            vals['salary_rule_id'] = self.env['hr.salary.rule'].search([('code', '=', vals['code'])]).id
        if 'code' in vals and vals['code'] == 'R_LOG':
            vals['salary_rule_id'] = self.env['hr.salary.rule'].search([('code', '=', 'R_INDML')]).id
        if 'code' in vals and vals['code'] == 'TRSPT_PRES':
            vals['salary_rule_id'] = self.env['hr.salary.rule'].search([('code', '=', 'TRSPT_PERS')]).id
        record = super(HrPayrollInput, self).write(vals)
        return record


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.depends('slip_ids')
    def recompute_sheets(self):
        self.slip_ids.compute_sheet()

    amount_total = fields.Integer("Salaire net global")
    move_id = fields.Many2one("account.move", "Pièce comptable bancaire", required=False)
    log_ids = fields.One2many("hr.payslip.run_log", 'slip_run_id', 'Logs')
    dispatched_ids = fields.One2many('hr.payslip_run.salary_dispatched', 'payslip_run_id',
                                     'Distribution de la masse salairale selon les banques')
    move_ids = fields.Many2many("account.move", "account_move_payslip_run", "slip_id", "move_id", "Pièces comptables")
    state = fields.Selection(selection_add=[('in_progress', 'En cours de validation'), ('rejected', 'Rejeté')])

    def send_notification(self, email_id, context=None):
        template_id = self.env['ir.model.data'].get_object_reference('hr_payroll_custom', email_id)
        try:
            mail_templ = self.env['mail.template'].browse(template_id[1])
            result = mail_templ.send_mail(res_id=self.id, force_send=True)
            return True
        except:
            return False

    def send_mail_payslip(self):
        slips = self.env['hr.payslip'].search([('state', '=', 'done')])
        email_template_id = self.env.ref('hr_payroll_custom.email_template_payslip').id
        email_template = self.env['mail.template'].browse(email_template_id)
        for slip in slips:
            email_template.send_mail(res_id=slip.employee_id.id, force_send=True)

    def close_payslip_run(self):
        for run in self:
            run.slip_ids.action_compute_slip_done()
            for slips in run.slip_ids:
                for slip in slips:
                    leaves = self.env['hr.leave'].search(
                        [('employee_id', '=', slip.employee_id.id), ('state', '=', 'validate'),
                         ('to_pay', '=', True), ('payslip_status', '=', False), ('holiday_status_id.code', '=', 'CONG')],
                        limit=1)
                    leaves.payslip_id = slip.id
                    leaves.to_pay = False
                    leaves.payslip_status = True
            run.state = 'close'
            self.send_notification('email_template_payslip')

    def _generate_account_bank_move(self):
        data = {
            'amount_total': 0,
            'lines': []
        }
        if self.slip_ids:
            amount_total = sum([x.get_amount_rubrique('NET') for x in self.slip_ids])
            data['amount_total'] = amount_total

            _query = """
            SELECT
                sum(d.amount) as amount,
                b.id as bank_id,
                b.name as bank_name
            FROM
                hr_payroll_salary_dispatched d
                LEFT JOIN res_bank b ON (d.bank_id = b.id)
            WHERE
                slip_id IN %(slip_ids)s
            GROUP BY
                b.name,
                b.id
            """

            _params = {
                'slip_ids': tuple(self.slip_ids.ids),
            }

            self.env.cr.execute(_query, _params)
            results = self.env.cr.dictfetchall()
            if results:
                for res in results:
                    val = {
                        'bank_id': res['bank_id'],
                        'amount': res['amount']
                    }
                    data['lines'].append(val)

        return data

    def action_rejected(self):
        for run in self:
            run.state = "rejected"

    def dispatched_slalary(self):
        for run in self:
            run.slip_ids.compute_dispatched_salary()
            if run.dispatched_ids:
                run.dispatched_ids.unlink()
            else:
                pass
            data = run._generate_account_bank_move()
            run.amount_total = data['amount_total']
            run.dispatched_ids = data['lines']

    def submit_to_validation(self):
        for run in self:
            run.state = "in_progress"

    def get_report_values(self, docids, data=None):
        docs = self.browse(docids['params']['id'])
        if docs.slip_ids:
            record = {
                'doc_ids': docids,
                'doc_model': 'hr.payslip.run',
                'docs': docs.slip_ids,
            }
            return record

        else:
            raise Warning("Il n'y a aucun bulletin à imprimer")


class HrPayslipRunLog(models.Model):
    _name = "hr.payslip.run_log"
    _description = "Gestion management"

    employee_id = fields.Many2one("hr.employee", "Employé")
    cause = fields.Char("Cause")
    slip_run_id = fields.Many2one("hr.payslip.run", "Lot de paie")


class HrLeave(models.Model):
    _inherit = "hr.leave"
