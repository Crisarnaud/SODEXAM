# -*- coding:utf-8 -*-

from odoo import api, models, fields, exceptions
from odoo.exceptions import ValidationError
import time
from datetime import date
from datetime import datetime, timedelta, date
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta


# Calculer le nombre de jours d'une date à une autre
def _get_number_of_days(date_echeance, date_demande):
    """fonction permettant de calculer la difference entre deux dates pour l'affichage du resulat en entier."""
    DATETIME_FORMAT = "%Y-%m-%d"
    from_dt = datetime.strptime (str (date_demande), DATETIME_FORMAT)
    to_dt = datetime.strptime (str (date_echeance), DATETIME_FORMAT)
    timedelta = str ((to_dt - from_dt).days)
    diff_day = int (timedelta) / 30
    return diff_day


class HrLoaningRequestWizard (models.TransientModel):
    _name = 'hr.loaning.request.wizard'
    _description = 'Echeanciers de paiement'

    def _default_employee(self):
        employee_id = self.env.context.get ('default_employee_id') or self.env['hr.employee'].search (
            [('user_id', '=', self.env.uid)], limit=1)
        return employee_id

    @api.model
    def create(self, vals):
        emp = self.env['hr.employee'].search ([('id', '=', vals.get ('employee_id'))])
        surfix = self.env['ir.sequence'].next_by_code ('hr.due.date')
        vals['name'] = 'ECHEANCE ' + '- ' + str (emp.name) + ' - ' + str (surfix)
        result = super (HrLoaningRequestWizard, self).create (vals)
        return result

    name = fields.Char ("Libellé de l'emprunt", size=150)
    employee_id = fields.Many2one ('hr.employee', 'Employé', required=True, ondelete='cascade',
                                   default=_default_employee)
    # job_id= fields.Many2one('hr.job', 'Poste', required=True)
    request_id = fields.Many2one ('hr.loaning.request', 'Demande', ondelete='cascade')
    deadline_ids = fields.One2many ('hr.loaning.line', 'loaning_id', 'Echéances', store=True)
    amount_loan = fields.Float ("Montant emprunt", size=20, required=True)
    date_loan = fields.Date ("Date d'emprunt")
    date_today = fields.Date (default=datetime.today ())
    reimbursement_start_date = fields.Date ('Date debut remboursement', required=True)
    deadline = fields.Date ("Date d'échéance")
    state_loan = fields.Boolean ('Reglé')
    total_loan = fields.Float ('Total à rembourser')
    rate = fields.Float ("Taux d'emprunt", help="Taux d'intérêt de remboursement", default=0.0)
    option = fields.Selection ([('lineaire', 'Linéaire')], 'Option échéance', readonly=False, required=True,
                               default='lineaire')
    expiry_number = fields.Integer ("Nombre d'échéance(s)", compute='compute_expiry_number', readonly=False)
    deadline_interval = fields.Selection ([('week', 'Hebdomadaire'), ('month', 'Mensuel')], 'Intervalle',
                                          readonly=False, default='month')
    notes = fields.Text ('Notes')
    state = fields.Selection (
        [('confirmed', 'Confirmé'), ('done', 'Terminé')],
        'Status', readonly=False, required=True, default='confirmed')

    @api.onchange ('amount_loan', 'rate')
    def compute_total_loan(self):
        """fonction permetant de calculer le montant a remboursé """
        if self.amount_loan != 0:
            self.total_loan = self.amount_loan + (self.amount_loan * (self.rate / 100))

    @api.onchange ('request_id')
    def compute_expiry_number(self):
        """
           #     La fonction qui permet de calculer les écheanciers de paiement en fonction de l'option choisie et aussi le calul du nombre d'echeance
           #     :return: deadline_ids : list
           #     """
        for record in self:

            lines = []
            record.deadline_ids = lines
            if record.request_id.date_deadline and record.request_id.date_request:
                record.expiry_number = _get_number_of_days (record.request_id.date_deadline,
                                                            record.request_id.date_request)
                if record.employee_id:
                    if record.option == 'lineaire':
                        if record.expiry_number != 0:
                            due = int (record.total_loan / record.expiry_number)
                            start = fields.Datetime.from_string (record.reimbursement_start_date)
                            for i in range (record.expiry_number):
                                value = {
                                    'loaning_id': record.id,
                                    'name': 'Remboursement de %s/%s' % (start.month, start.year),
                                    'scheduled_date': str (start),
                                    'date_reimbursement_due': False,
                                    'state_loan': 'take',
                                    'amount': due
                                }
                                lines += [value]
                                if record.deadline_interval == 'month':
                                    start += relativedelta (months=+1)
                                else:
                                    start += relativedelta (weeks=+1)
                    else:
                        pass
                    record.deadline_ids = record.deadline_ids.create (lines)

    def computeLoaning(self):
        self.ensure_one ()
        if self.type == 'lineaire':
            return True
        else:
            return True

    def action_confirmed(self):
        if self.demande_id:
            self.demande_id.action_validated ()
        self.state = 'done'

    def action_validate_deadline(self):
        """fonction pour la validation de l'echéancier"""
        for record in self:
            if record.request_id.state == 'validated':
                lines = []

                for deadline in record.deadline_ids:
                    lines.append((0, 0, {
                        'name': deadline.name,
                        'scheduled_date': deadline.scheduled_date,
                        'date_reimbursement_due': deadline.date_reimbursement_due,
                        'amount': deadline.amount,
                        'amount_paid': deadline.amount_paid,
                        'state_loan': 'take'
                    }))
                record.request_id.write({
                    'state': 'echeance',
                    'deadline_ids': lines,
                    'expiry_number': record.expiry_number,
                    'reimbursement_start_date':record.reimbursement_start_date,
                    'option' : record.option,
                    'deadline_interval': record.deadline_interval,
                    'rate': record.rate,
                    'total_loan': record.total_loan,
                })


class HrLoaningLine (models.TransientModel):
    _name = 'hr.loaning.line'
    _description = "Lignes d'echeanciers de paiement"

    def _get_solde_deadline(self):
        for mont in self:
            mont.montant_restant = mont.montant - mont.montant_paye


    name = fields.Char ('Nom', readonly=True, store=True)
    scheduled_date = fields.Date ('Date de prélèvement', readonly=True, store=True)
    date_reimbursement_due = fields.Date ('Date de paiement', readonly=False, store=True)
    amount = fields.Integer ('Montant', readonly=True, store=True, default=0)
    amount_paid = fields.Integer ('Montant payé', readonly=False, default=0)
    sum_remaining = fields.Integer ('Reste à payer', readonly=False, compute='_get_solde_echeance', store=True)
    state_loan = fields.Selection ([('take', 'A prelever'), ('taked', 'Prélévé'), ('paid', 'Payé')],
                                   'Status', store=True)
    loaning_id = fields.Many2one ('hr.loaning.request.wizard', 'Écheancier', required=False)



class HrDocbox (models.TransientModel):
    _name = "hr.doc.box"
    _description = "Payment at checkout"

    def _get_line_id(self):
        return self.env.context.get ('active_id')

    reference = fields.Char ('Référence', size=64, readonly=False)
    name = fields.Char ('Libellé document', size=64, readonly=False)
    reference = fields.Char ('Référence', size=64, readonly=False)
    attachment_ids = fields.Many2many ("ir.attachment", "rel_employee_attachment", "h_id", "a_id",
                                       string="Pièces jointes")
    line_id = fields.Many2one ('hr.deadline.line', 'Remboursement :', required=False, readonly=True,
                               default=_get_line_id)

    def action_validate_box(self):
        """ecriture sur le formulaire de l'echeancier pour le paiement à la caisse"""
        for record in self:
            if record.line_id.state_loan == 'take':
                record.line_id.write ({
                    'state_loan': 'paid',
                    'amount_paid': record.line_id.amount,
                    'amount': 0,
                    'name_box': record.name,
                    'reference_box': record.reference,
                    'attachment_ids': record.attachment_ids,
                })

