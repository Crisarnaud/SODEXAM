# -*- coding:utf-8 -*-


from odoo import api, fields, models, _
import logging

_logger = logging.getLogger (__name__)


class HrEmployee (models.Model):
    _inherit = 'hr.employee'

    def get_amount_emprunt(self, date_from, date_to):
        """fonction pour la prise en compte de la ligne d'echance du prêt scolaire concerné selon la periode de la fiche de paie
        date_from date_to"""
        loaning_obj = self.env['hr.loaning.request']
        amount = 0
        if date_from and date_to:
            loanings = loaning_obj.search ([('employe_id', '=', self.id)])
            if loanings:
                for loaning in loanings:
                    echeances = loaning.deadline_ids.filtered (
                        lambda r: (r.scheduled_date <= date_to and r.scheduled_date >= date_from) and r.state_loan == "take")
                    if echeances:
                        amount = sum ([ech.amount for ech in echeances])
        return amount

    def get_advanced_salary_monthly(self, date_from, date_to):
        """fonction pour la prise en compte de la ligne d'échance de l'avance sur salaire concerné pour la periode de la fiche de paie
        date_from date_to"""
        as_obj = self.env['hr.advance.salary']
        amount = 0
        if date_from and date_to:
            advance_salaries = as_obj.search ([('employee_id', '=', self.id)])
            if advance_salaries:
                for advance in advance_salaries:
                    advances = advance.filtered (
                        lambda r: r.date <= date_to and r.date >= date_from)
                    if advances and advance.state == 'done':
                        amount = sum ([ad.amount for ad in advances])
        return amount

    def getInputsPayroll(self, contract, date_from, date_to):
        """ fonction permettant d'inserer l'avance sur salaire et le prêt scolaire sur la
        fiche de paie pour le calcul"""
        res = super (HrEmployee, self).getInputsPayroll (contract, date_from, date_to)
        avs = self.get_advanced_salary_monthly (date_from, date_to)
        input_avs = self.env['hr.salary.rule'].search ([('code', '=', 'SAL_AV')], limit=1)
        if avs != 0:
            val = {
                'name': "Avance sur salaire",
                'code': "SAL_AV",
                'amount': avs,
                'contract_id': contract.id,
                'salary_rule_id': input_avs.id,
            }
            res += [val]

        emprunts = self.get_amount_emprunt (date_from, date_to)
        input_emprunt = self.env['hr.salary.rule'].search ([('code', '=', 'EMP')], limit=1)
        if emprunts != 0:
            val = {
                'name': "Emprunt à déduire sur le salaire",
                'code': "EMP",
                'amount': emprunts,
                'contract_id': contract.id,
                'salary_rule_id': input_emprunt.id,
            }
            res += [val]
        return res


class HrPayslip (models.Model):
    _inherit = 'hr.payslip'
    def compute_sheet(self):
        result = super(HrPayslip, self).compute_sheet()
        as_obj = self.env['hr.advance.salary'].search([('employee_id', '=', self.employee_id.id)])
        for slip in as_obj:
            if slip.state == 'done':
                slip.state = 'end'
        return result


