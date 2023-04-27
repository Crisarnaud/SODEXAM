# -*- coding:utf-8 -*-

import time
from datetime import date
from datetime import datetime, timedelta, date
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from odoo import models, api, fields, _, exceptions

from odoo.exceptions import ValidationError
from odoo import fields, osv, api, models
from odoo import tools
from odoo.tools.translate import _

import logging

_logger = logging.getLogger (__name__)


class ResCompany (models.Model):
    _inherit = 'res.company'

    number_maximum_amount = fields.Integer ("Nombre calcul prêt", default=2, help="Nombre permettant de calculer la somme maximale à prendre comme prêt",store=True)


class HrContract (models.Model):
    _inherit = 'hr.contract'

    @api.onchange ('wage', 'sursalaire', 'hr_payroll_prime_ids')
    def compute_amount_max(self):
        """fonction onchange  pour la contrainte sur le montant  maximal à prendre comme prêt selon ses primes son salaire categoriel et son sursalaire
        maximum_amount"""
        amount_max = []
        for record in self:
            bonus_transport = record.employee_id.company_id.bonus_transport
            number_maximum_amount = record.employee_id.company_id.number_maximum_amount
            record.maximum_amount = (record.wage + record.sursalaire) * number_maximum_amount
            for prime in record.hr_payroll_prime_ids:
                if prime.code != 'TRSP':
                    amount_max.append (prime.montant_prime)
                    record.maximum_amount = ((record.wage + record.sursalaire) + sum (amount_max)) * number_maximum_amount
                else:
                    if prime.code == 'TRSP':
                        if prime.montant_prime > bonus_transport:
                            amount_max.append (prime.montant_prime)
                            record.maximum_amount = (((record.wage + record.sursalaire) + sum (
                                amount_max) ) - bonus_transport) * number_maximum_amount

    @api.onchange ('wage', 'sursalaire', 'hr_payroll_prime_ids')
    def compute_amount_advance_salary(self):
        """fonction onchange  pour la contrainte sur le montant  maximal à prendre comme avance sur salaire selon ses primes son salaire categoriel et son sursalaire
        maximum_amount"""
        amount_advance_salary = []
        for record in self:
            bonus_transport = record.employee_id.company_id.bonus_transport
            record.maximum_amount_advance_salary = (record.wage + record.sursalaire)
            for prime in record.hr_payroll_prime_ids:
                if prime.code != 'TRSP':
                    amount_advance_salary.append (prime.montant_prime)
                    record.maximum_amount_advance_salary = ((record.wage + record.sursalaire) + sum (
                        amount_advance_salary))
                else:
                    if prime.code == 'TRSP':
                        if prime.montant_prime > bonus_transport:
                            amount_advance_salary.append (prime.montant_prime)
                            record.maximum_amount_advance_salary = (((record.wage + record.sursalaire) + sum (
                                amount_advance_salary)) - bonus_transport)

    maximum_amount = fields.Float ('Montant prêt', compute='compute_amount_max', help= "Montant maximal à prendre pour un prêt scolaire")
    maximum_amount_advance_salary = fields.Float ('Montant avance sur salaire', compute='compute_amount_advance_salary',
                                   help="Montant maximal à prendre pour une avance sur salaire")


class HrLoaningRequest (models.Model):
    _name = 'hr.loaning.request'
    _description = "Demande d'emprunt"

    def _default_employee(self):
        employee_id = self.env.context.get ('default_employee_id') or self.env['hr.employee'].search (
            [('user_id', '=', self.env.uid)], limit=1)
        return employee_id

    @api.constrains ('amount_request')
    def _check_amount_request(self):
        """fonction contrainte sur le montant pris par l'employé"""
        for record in self:
            if record.amount_request > record.employe_id.contract_id.maximum_amount:
                raise ValidationError (
                    "Le montant du prêt doit être inférieur au montant maximale à prendre qui est  de %s" % (
                        record.employe_id.contract_id.maximum_amount))
            if record.amount_request and record.amount_request < 0:
                raise ValidationError ("Votre montant doit être supérieur à 0")

    @api.constrains ('employe_id')
    def _check_employee(self):
        """fonction contrainte sur le prise de l'employé ayant un prêt"""
        for record in self:
            if record.employe_id:

                domain = [
                    ('employe_id', '=', record.employe_id.id),
                    ('date_request', '<=', record.date_deadline),
                    ('date_deadline', '>=', record.date_request),
                    ('id', '!=', record.id),
                    ('state', 'in',
                     ['validated', 'echeance']),
                ]
            loan = self.search_count (domain)
            if loan > 0 :
                raise ValidationError ( "Vous avez une demande de prêt dans cette même periode car l'employé dispose déjà d'un prêt")

    @api.model
    def create(self, vals):
        """fonction create pour le nom du prêt en prenant en compte la date et la séquence"""
        emp = self.env['hr.employee'].search ([('id', '=', vals.get ('employe_id'))])
        surfix = self.env['ir.sequence'].next_by_code ('hr.loaning.request')
        vals['name'] = 'PRÊT SCOLAIRE  ' + '- ' + str (emp.name) + ' - ' + str (surfix)
        result = super (HrLoaningRequest, self).create (vals)
        return result

    name = fields.Char ("Libellé", size=150, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    employe_id = fields.Many2one ('hr.employee', 'Employe', ondelete='cascade', default=_default_employee, index=True,
                                  readonly=False,
                                  states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    job_id = fields.Many2one ('hr.job', 'Poste', ondelete='cascade', related='employe_id.job_id', readonly=True)
    user_id = fields.Many2one ('res.users', 'Demandeur', required=True, related_sudo=True, store=True,
                               default=lambda self: self.env.uid, readonly=True)
    reason_request = fields.Char ("Motif", size=150, default="Prêt scolaire")
    amount_request = fields.Float ("Montant", size=20)
    date_request = fields.Date ("Date d'emprunt", default=datetime.today ())
    date_deadline = fields.Date ("Date d'échéance",
                                 default=datetime (datetime.today ().year, 7, 31) + relativedelta (years=+1),
                                 store=True)
    note = fields.Text ('Notes')
    state = fields.Selection (
        [('draft', 'Brouillon'), ('validated', 'Validé'),
         ('echeance', 'Echéance'), ('done', 'Clôturé')], 'Statut', default='draft')
    contract_id = fields.Many2one ('hr.contract')
    deadline_ids = fields.One2many ('hr.deadline.line', 'request_id')
    expiry_number = fields.Integer ("Nombre d'echeance")
    deadline_interval = fields.Selection ([('week', 'Hebdomadaire'), ('month', 'Mensuel')], 'Intervalle')
    reimbursement_start_date = fields.Date ("")
    option = fields.Char ("")
    rate = fields.Float ("")
    total_loan = fields.Integer ("")

    def action_confirmed(self):
        self.state = 'confirmed'

    def action_validated(self):
        self.state = 'validated'

    def action_cancel(self):
        self.state = 'cancel'

    def action_done(self):
        if self.state == 'echeance':
            self.state = 'done'

    def action_generate_loaning(self):
        """fonction pour generer l'echeancier a partir de la demande"""
        emp_obj = self.env['hr.loaning.request.wizard']
        for request in self:
            loan = {
                'name': 'Emprunt de %s' % (request.employe_id.name),
                'employee_id': request.employe_id.id,
                'date_loan': request.date_request,
                'deadline': request.date_deadline,
                'reimbursement_start_date': request.date_request,
                'amount_loan': request.amount_request,
                'total_loan': request.amount_request,
                'state_loan': False,
                'option': 'lineaire',
                'request_id': request.id,
            }
            emp_id = emp_obj.create (loan)
            modid = self.env['ir.model.data'].get_object_reference ('loan_custom', 'loaning_form_wizard_view')
            result = {
                'name': _ ("Echéancier de paiement"),
                'view_mode': 'form',
                'view_id': modid[1],
                'view_type': 'form',
                'res_model': 'hr.loaning.request.wizard',
                'type': 'ir.actions.act_window',
                'domain': '[]',
                'res_id': emp_id.id,
                'context': {'active_id': emp_id.id},
                'target': 'new',
            }

            return result


class HrDeadlineLine (models.Model):
    _name = 'hr.deadline.line'
    _description = "Lignes d'echeanciers de paiement"

    name = fields.Char ('Nom', readonly=True, store=True)
    scheduled_date = fields.Date ('Date de prélèvement', readonly=True, store=True)
    date_reimbursement_due = fields.Date ('Date de paiement', readonly=False, store=True)
    amount = fields.Integer ('Montant', readonly=True, store=True, default=0)
    amount_paid = fields.Integer ('Montant payé', readonly=False, default=0)
    sum_remaining = fields.Integer ('Reste à payer', readonly=False, store=True)
    state_loan = fields.Selection ([('take', 'A préléver'), ('taked', 'Prélévé'), ('paid', 'Payé')],
                                   'Status', store=True)
    request_id = fields.Many2one ('hr.loaning.request', 'Écheancier', required=False)
    name_box = fields.Char ('Libellé document')
    reference_box = fields.Char ('Référence')
    attachment_ids = fields.Many2many ("ir.attachment", "rel_box_attachment", "c_id", "b_id",
                                       string="Pièces jointes")


