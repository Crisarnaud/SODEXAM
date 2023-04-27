# -*- coding:utf-8 -*-


import time
import babel
from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models, exceptions, tools, _
import logging

_logger = logging.getLogger(__name__)


class HrReversePrime(models.TransientModel):
    _name = "hr.reverse.prime"
    _description = "hr.reverse.prime"

    @api.depends('prime_id')
    def _get_code_prime(self):
        if self.prime_id:
            self.code = self.prime_id.code

    prime_id = fields.Many2one('hr.payroll.prime', 'prime', required=True)
    hr_reverse_contract_id = fields.Many2one('hr.reverse.contract', 'Contract')
    montant_prime = fields.Integer('Montant', required=True)


class HrReverseContract(models.TransientModel):
    _name = 'hr.reverse.contract'
    _description = "Contrat inverse"

    name = fields.Selection([('brut', 'Par le brut'), ('net', 'Par le net')], 'Méthode de calcul', requred=True)
    prime_ids = fields.One2many('hr.reverse.prime', 'hr_reverse_contract_id', 'Primes', required=True)
    hr_convention_id = fields.Many2one('hr.convention', "Convention", required=False)
    hr_secteur_id = fields.Many2one('hr.secteur.activite', "Secteur d'activité", required=False)
    categorie_salariale_id = fields.Many2one('hr.categorie.salariale', 'Catégorie salariale', required=False)
    wage = fields.Float('Salaire de Base', required=False)
    sursalaire = fields.Integer("Sursalaire", required=False)
    prime_anciennete = fields.Integer("Prime d'anciennété")
    type_calcul = fields.Selection([('brut', 'Par le brut imposable'), ('net', 'Par le net')], 'Méthode de calcul', requred=True)
    montant = fields.Integer("Montant ")
    contract_id = fields.Many2one('hr.contract', 'Contrat')
    payslip = fields.Many2one('hr.payslip', 'Bulletin de paie')

    @api.onchange("hr_convention_id")
    def on_change_convention_id(self):
        if self.hr_convention_id:
            return {'domain': {'hr_secteur_id': [('hr_convention_id', '=', self.hr_convention_id.id)]}}
        else:
            return {'domain': {'hr_secteur_id': [('hr_convention_id', '=', False)]}}

    @api.onchange("hr_secteur_id")
    def on_change_secteur_id(self):
        if self.hr_secteur_id:
            return {'domain': {'categorie_salariale_id': [('hr_secteur_activite_id', '=', self.hr_secteur_id.id)]}}
        else:
            return {'domain': {'categorie_salariale_id': [('hr_secteur_activite_id', '=', False)]}}

    @api.onchange('categorie_salariale_id')
    def on_change_categorie_salariale_id(self):
        if self.categorie_salariale_id:
            self.wage = self.categorie_salariale_id.salaire_base

    def _get_lines(self):
        active_id = self._context.get('active_id')
        if active_id:
            contract = self.env['hr.contract'].browse(active_id)
            if contract:
                return [
                    (0, 0, {'prime_id': input.id})
                    for input in contract.hr_payroll_prime_ids
                ]
        return []

    def compute(self):
        payslip_obj = self.env['hr.payslip']
        contract = self.env['hr.contract'].browse(self._context.get('active_id'))
        total_intrant = contract.wage
        bonus_transport_contract = 0
        sursalaire = 0
        for prime in contract.hr_payroll_prime_ids:
            total_intrant += prime.montant_prime
            if prime.code == 'TRSP':
                bonus_transport_contract = prime.montant_prime
        if total_intrant > self.montant:
            raise exceptions.ValidationError('Le montant est inféreur aux intrants')
        else:
            structure_salariale = contract.struct_id
            use_anc = False
            now = datetime.now()
            date_from = datetime(now.year, now.month, 1)
            date_to = date_from + relativedelta.relativedelta(months=1, days=-1)
            inputs = payslip_obj.get_inputs(contract, date_from, date_to)
            input_line_ids = []
            if inputs:
                for input in inputs:
                    temp = [0, False, input]
                    input_line_ids += [temp]
            worked_days = payslip_obj.get_worked_days(contract, date_from, date_to)
            worked_days_line_ids = []
            if worked_days:
                for worked_day in worked_days:
                    temp = [0, False, worked_day]
                    worked_days_line_ids += [temp]
                    locale = self.env.context.get('lang') or 'en_US'
            vals = {
                'name': _('Salary Slip of %s for %s') % (
                    contract.employee_id.name, tools.ustr(
                        babel.dates.format_date(date=date_from, format='MMMM-y', locale=locale))),
                'employee_id': contract.employee_id.id,
                'date_from': date_from,
                'date_to': date_to,
                'contract_id': contract.id,
                'struct_id': contract.struct_id.id,
                'input_line_ids': input_line_ids,
                'worked_days_line_ids': worked_days_line_ids,
            }
            payslip_id = payslip_obj.create(vals)
            payslip_id.compute_sheet()
            if self.type_calcul == 'brut':
                for rule in structure_salariale.rule_ids:
                    if rule.code == 'PANC':
                        use_anc = True
                        break
                if contract.employee_id and contract.employee_id.company_id.bonus_transport:
                    bonus_transport_legal = contract.employee_id.company_id.bonus_transport
                else:
                    raise exceptions.ValidationError(_("Verifier que le contrat {} est rattaché à un employé et que le "
                                                       "montant de la prime de transport est bien définie dans les "
                                                       "données de la société.".format(contract.name)))
                if bonus_transport_contract :

                    if bonus_transport_contract > bonus_transport_legal:
                        total_intrant -= bonus_transport_legal
                    if use_anc:
                        prime_anciennete = 0.0
                        if 1 < self.contract_id.an_anciennete:
                            prime_anciennete = 0.01 * contract.wage * min(contract.an_anciennete, 25)
                        total_intrant += prime_anciennete
                brut_add = self.montant - total_intrant
                brut_amount = payslip_id.get_brut_amount()
                while brut_amount != self.montant:
                    if brut_amount < self.montant:
                        brut_add += self.montant - brut_amount
                    elif brut_amount > self.montant:
                        brut_add -= (brut_amount - self.montant)
                    contract.sursalaire = brut_add
                    payslip_id.compute_sheet()
                    brut_amount = payslip_id.get_brut_amount()
            elif self.type_calcul == 'net':
                net_amount = payslip_id.get_net_paye()
                while net_amount != self.montant:
                    net_amount = payslip_id.get_net_paye()
                    if net_amount < self.montant:
                        sursalaire += self.montant - net_amount
                    elif net_amount > self.montant:
                        sursalaire -= net_amount - self.montant
                    contract.sursalaire = sursalaire
                    payslip_id.compute_sheet()
        # payslip_id.unlink()

