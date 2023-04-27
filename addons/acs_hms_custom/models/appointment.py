from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger (__name__)


class HmsAppointment (models.Model):
    _inherit = 'hms.appointment'

    prescription_end_date = fields.Date (string="Date de validité", compute='get_prescription_end_date', store=True)
    patient_confirmation_mobile_number = fields.Char (string='Code de confirmation', related='patient_id.code',
                                                      store=True)
    speciality_id = fields.Many2one ('physician.specialty', related='physician_id.specialty_id', store=True,
                                     string="spécialité")
    company_id = fields.Many2one ('res.company')
    consultation_nas = fields.Boolean ('Est un employé Nas ou Sodexam?', default=False, store=True)
    user_id = fields.Many2one ('res.users', string='Responsable',
                               ondelete='cascade',
                               help='Responsible User for appointment validation And further Followup.',
                               default=lambda self: self.env.user)

    def back_to_draft(self):
        """
        Function to return the workflow to draft
        Returns:

        """
        if self.state == 'waiting':
            self.state = 'confirm'

    @api.onchange ('patient_id')
    def onchange_patient_id(self):
        super (HmsAppointment, self).onchange_patient_id ()
        for rec in self:
            if rec.patient_id.corpo_company_id.code_company == 'nas' or rec.patient_id.corpo_company_id.code_company == 'sdx':
                rec.consultation_nas = True
            else:
                rec.consultation_nas = False
        return False

    def create_invoice(self):
        """
        inherit create invoice function to modify his action:
        To verify if his invoices is paid.
        Returns:

        """
        value = self.company_id.acs_check_appo_payment
        self.company_id.acs_check_appo_payment = True
        res = super (HmsAppointment, self).create_invoice ()
        lines_to_update = []
        if self.consultation_nas == True:
            if self.speciality_id.code_speciality == 'GEN':
                for line in self.invoice_id.invoice_line_ids:
                    lines_to_update.append ((1, line.id, {'price_unit': self.company_id.price_of_customer_nas_gen}))
                self.invoice_id.update ({'invoice_line_ids': lines_to_update})
                move = self.env['account.move'].search ([('invoice_origin', '=', str (self.name))])
                for rec in move:
                    if self.insurance_id and self.insurance_company_id.partner_id.id == rec.partner_id.id:
                        for line in rec.invoice_line_ids:
                            lines_to_update.append (
                                (1, line.id, {'price_unit': self.company_id.price_of_insurance_gen}))
                        rec.update ({'invoice_line_ids': lines_to_update})
            elif self.speciality_id.code_speciality != 'GEN':
                for line in self.invoice_id.invoice_line_ids:
                    lines_to_update.append ((1, line.id, {'price_unit': self.company_id.price_of_customer_nas_spe}))
                self.invoice_id.update ({'invoice_line_ids': lines_to_update})
                if self.insurance_id:
                    percent_customer = 100 - self.insurance_id.app_insurance_percentage
                    for line in self.invoice_id.invoice_line_ids:
                        lines_to_update.append ((1, line.id, {
                            'price_unit': self.company_id.price_of_customer_nas_spe * percent_customer / 100}))
                    self.invoice_id.update ({'invoice_line_ids': lines_to_update})
                    move = self.env['account.move'].search ([('invoice_origin', '=', str (self.name))])
                    for rec in move:
                        if self.insurance_company_id.partner_id.id == rec.partner_id.id:
                            for line in rec.invoice_line_ids:
                                lines_to_update.append (
                                    (1, line.id, {
                                        'price_unit': self.company_id.price_of_customer_nas_spe * self.insurance_id.app_insurance_percentage / 100}))
                            rec.update ({'invoice_line_ids': lines_to_update})
        return res

    @api.depends ('date', 'patient_confirmation_mobile_number', 'speciality_id')
    def get_prescription_end_date(self):
        """
        Method to add automatically the validated date
        to allow the patient to go to consultations free of charge during the two weeks following his last consultation

        Returns:
        """
        for rec in self:
            appointment_id = self.search ([('patient_id', '=', rec.patient_id.name),
                                           ('patient_confirmation_mobile_number', '=',
                                            self.patient_confirmation_mobile_number),
                                           ('state', '!=', 'draft'), ('speciality_id', '=', self.speciality_id.name)],
                                          order='date desc', limit=1)
            today_date = datetime.datetime.today ().strftime ('%Y-%m-%d')
            if appointment_id and str (today_date) <= str (
                    datetime.datetime.strptime (str (appointment_id.prescription_end_date), '%Y-%m-%d').date ()):
                rec.prescription_end_date = appointment_id.prescription_end_date

            else:
                start_date = datetime.datetime.strptime (str (rec.date), '%Y-%m-%d %H:%M:%S').date ()
                end_date = start_date + datetime.timedelta (rec.company_id.number_of_days_validates)
                rec.prescription_end_date = end_date

    def appointment_confirm(self):
        """
        inherit appointment confirm function to modify his action:
        To verify if the patient is going to consultations for free or not
        Returns:

        """
        appointment_id = self.search ([('patient_id', '=', self.patient_id.name),
                                       ('patient_confirmation_mobile_number', '=',
                                        self.patient_confirmation_mobile_number),
                                       ('state', '!=', 'draft'), ('speciality_id', '=', self.speciality_id.name)],
                                      order='date desc', limit=1)
        today_date = datetime.datetime.today ().strftime ('%Y-%m-%d')

        if appointment_id and str (today_date) <= str (
                datetime.datetime.strptime (str (appointment_id.prescription_end_date), '%Y-%m-%d').date ()):
            self.state = 'confirm'

        else:
            res = super (HmsAppointment, self).appointment_confirm ()
            if self.invoice_id and self.payment_state not in ['in_payment', 'paid']:
                raise UserError (_ ('Invoice is not Paid yet.'))
            return res


class PhysicianSpeciality (models.Model):
    _inherit = 'physician.specialty'

    code_speciality = fields.Char ('Code Specialité', store=True)
