# -*- coding:utf-8 -*-

from odoo import api, models, fields, _, exceptions


class HrEmployeeSalaryDispatched(models.Model):
    _name = "hr.employee.salary.dispatched"
    _description = "Distribution salariale"

    name = fields.Char('Désignation', required=True)
    employee_id = fields.Many2one('hr.employee', "employé", required=True)
    active = fields.Boolean('Actif', default=True)


class HrEmployeeSalaryDispatchedLine(models.Model):
    _name = "hr.employee.salary.dispatched.line"
    _description = "Ligne de distribution salariale"
    _order = "sequence"
    _rec_name = "bank_id"

    bank_id = fields.Many2one('res.partner.bank', 'Compte bancaire', required=True, ondelete='cascade')
    type = fields.Selection([('balance', 'Balance'), ('fix', 'Montant fix'),
                             ('perc', 'Pourcentage')], 'Type', default='balance')
    type_operation = fields.Selection([('courant', "Compte courant/Épargne"), ('credit', 'Remboursement Prêt')])
    sequence = fields.Integer("Séquence", default=10)
    amount = fields.Float('Montant ou %', default=0.0,
                          help="Mettez soit le montant (ex. 100 000) ou le pourcentage (25%)")
    employee_id = fields.Many2one('hr.employee', "Employé", required=False)
    description = fields.Text("Commentaire", required=False)

    @api.constrains('amount', 'type')
    def _check_percentage(self):
        for rec in self:
            records = self.env['hr.employee.salary.dispatched.line'].search([('employee_id', '=', rec.employee_id.id)])
            count_type_balance = 0
            cumulative_percentages = 0
            for record in records:
                if record.type == 'perc' and (100 >= record.amount <= 0):
                    raise exceptions.ValidationError(_("Le pourcentage doit être supérieur à 0% inférieur 100%. "
                                                       "Merci de faire les corrections nécessaires"))
                if record.type == 'perc':
                    cumulative_percentages += record.amount
                if record.type == 'balance':
                    count_type_balance += 1
            if cumulative_percentages >= 100:
                raise exceptions.ValidationError(_("Le cumul des pourcentage doit être inférieur à 100%. Mais vous "
                                                   "avez exactement {} %. Merci de faire les corrections nécessaires"
                                                   .format(cumulative_percentages)))
            if count_type_balance == 0 or count_type_balance > 1:
                raise exceptions.ValidationError(_("Il doit avoir un compte ayant le type 'Balance'. Mais vous "
                                                   "avez exactement {}. Merci de faire le nécessaire"
                                                   .format(count_type_balance)))


class HrPayrollSalaryDispatched(models.Model):
    _name = "hr.payroll.salary_dispatched"
    _description = "Distribution du salaire sur le bulletin"

    slip_id = fields.Many2one('hr.payslip', 'Bullétin de paie', required=False)
    account_bank_id = fields.Many2one('res.partner.bank', 'Compta bancaire', required=False)
    bank_id = fields.Many2one('res.bank', "Banque", required=False)
    amount = fields.Float("Montant à virer", required=True)
