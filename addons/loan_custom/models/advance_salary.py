#-*- coding:utf-8 -*-

from odoo import api, models, fields, exceptions
from odoo.exceptions import ValidationError

class HrAdvanceSalary(models.Model):
    _name = 'hr.advance.salary'
    _description = "Avance sur salaire"
    _order = 'id desc'

    @api.model
    def create(self, vals):
        emp = self.env['hr.employee'].search ([('id', '=', vals.get ('employee_id'))])
        surfix = self.env['ir.sequence'].next_by_code ('hr.advance.salary')
        vals['name'] = 'AVANCE SUR SALAIRE ' + '- ' + str (emp.name) + ' - ' + str (surfix)
        result = super (HrAdvanceSalary, self).create (vals)
        return result

    name= fields.Char('Designation', size=255)
    employee_id= fields.Many2one('hr.employee', 'Employé')
    date= fields.Date("Date")
    state= fields.Selection([('draft', 'Brouillon'),('done', 'Validé'),('cancel', 'Annulé'),('end', 'Terminé')
                             ], 'Status', default='draft', store=True)
    amount= fields.Integer('Montant')

    @api.constrains ('amount')
    def _check_amount(self):
        """Fonction permettant d'éffectuer des contraintes sur le montant à prendre"""
        for record in self:
            if record.amount <= 0:
                raise ValidationError ("Votre montant doit être supérieur à 0")
            if record.amount > record.employee_id.contract_id.maximum_amount_advance_salary:
                raise ValidationError (
                    "Le montant du prêt doit être inférieur au montant maximale à prendre qui est  de %s" % (
                        record.employee_id.contract_id.maximum_amount_advance_salary))


    def action_draft(self):
        for res in self:
            res.state = 'draft'


    def action_done(self):
        for res in self:
            res.state = 'done'


    def action_cancel(self):
        for res in self:
            res.state = 'cancel'

    def action_end(self):
        for res in self:
            res.state = 'end'

