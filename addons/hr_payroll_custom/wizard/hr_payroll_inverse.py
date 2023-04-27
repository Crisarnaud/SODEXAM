# -*- coding:utf-8 -*-
from math import ceil

from odoo import api, fields, models, exceptions


class HrPayrollInverse(models.TransientModel):
    _name = 'hr.payroll.inverse'
    _description = "Calcul inverse la paye"

    def _get_lines(self):
        active_id = self._context.get('active_id')
        if active_id:
            slip = self.env['hr.payslip'].browse(active_id)
            if slip:
                return [
                    (0, 0, {'rule_id': input.id})
                    for input in slip.input_line_ids
                ]

        return []

    def computeSlip(self):
        payslip = self.env['hr.payslip'].browse(self._context.get('active_id'))
        contract = payslip.contract_id
        total_intrant = contract.wage
        bonus_transport_contract = 0
        input = 0
        for prime in contract.hr_payroll_prime_ids:
            total_intrant += prime.montant_prime
            if prime.code == 'TRSP':
                bonus_transport_contract = prime.montant_prime

        if total_intrant > self.montant:
            print('L35 ',total_intrant)
            raise exceptions.Warning('Le montant est inféreur aux intrants')
        else:
            structure_salariale = payslip.struct_id
            if self.type_calcul == 'brut':
                use_anc = False
                for rule in structure_salariale.rule_ids:
                    if rule.code == 'PANC':
                        use_anc = True
                        break
                bonus_transport_legal = contract.employee_id.company_id.bonus_transport
                if bonus_transport_contract > bonus_transport_legal:
                    total_intrant -= bonus_transport_legal
                if use_anc:
                    prime_anciennete = 0.0
                    if 1 < contract.an_anciennete:
                        prime_anciennete = 0.01 * contract.wage * min(contract.an_anciennete, 25)
                    total_intrant += prime_anciennete

                input = self.montant - total_intrant
                brut_amount = payslip.get_brut_amount()
                while brut_amount != self.montant:
                    if brut_amount < self.montant:
                        input += self.montant - brut_amount
                    elif brut_amount > self.montant:
                        input -= (brut_amount - self.montant)
                    contract.sursalaire = input
                    payslip.compute_sheet()
                    brut_amount = payslip.get_brut_amount()
            elif self.type_calcul == 'net':
                net_amount = payslip.get_net_paye()
                while net_amount != self.montant:
                    net_amount = payslip.get_net_paye()
                    if net_amount < self.montant:
                        input += self.montant - net_amount
                    else:
                        input -= (net_amount - self.montant)
                    contract.sursalaire = ceil(input)
                    payslip.compute_sheet()

    line_ids = fields.One2many('hr.payroll.inverse.line', 'inverse_id', 'Lignes', required=False, default=_get_lines)
    type_calcul = fields.Selection([('brut', 'Par le brut imposable'), ('net', 'Par le net')], 'Méthode de calcul',
                                   requred=True)
    montant = fields.Integer("Montant ")


class HrPayrollInverseLine(models.TransientModel):
    _name = 'hr.payroll.inverse.line'
    _description = "Ligne de calcul inverse de la paye"

    rule_id = fields.Many2one('hr.payslip.input', 'Règle salariale', required=False)
    inverse_id = fields.Many2one('hr.payroll.inverse', 'Calcul inverse', required=False)
