# -*- coding:utf-8 -*-

from odoo import api, fields, models, _, exceptions


class HrPayrollAnanlyse(models.Model):
    _name = 'hr.payroll.analyse'
    _description = "Analyse de la paie"

    employee_id = fields.Many2one('hr.employee', 'Employé', required=True)
    slip_id = fields.Many2one('hr.payslip', 'Bulletin de paie', required=True, ondelete='cascade')
    date = fields.Date('Date', required=True)
    base = fields.Integer('Salaire de Base', default=0)
    sursalaire = fields.Integer('Sursalaire', default=0)
    primes = fields.Integer('Total prime', default=0)
    brut = fields.Integer('Brut', default=0)
    retenues = fields.Integer('Total retenue employé', default=0)
    transport = fields.Integer('Transport', default=0)
    net_paie = fields.Integer('Net de paie', default=0)
    emprunt = fields.Integer('Emprunts employés', default=0)
    net = fields.Integer('Net', default=0)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    def generateLine(self, slip_id):
        return True
