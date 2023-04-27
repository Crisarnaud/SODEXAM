# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
import xlrd
import base64
import logging

_logger = logging.getLogger (__name__)


class AcsLaboratoryRequest (models.Model):
    _inherit = 'acs.laboratory.request'

    state = fields.Selection (
        [('draft', 'Brouillon'), ('accepted', 'Facturation'), ('to_invoice', 'A facturer'),
         ('done', 'Terminé'), ('cancel', 'Annulé')], string='Statut', default='draft')

    insurance_id = fields.Many2one ('hms.patient.insurance', string='Insurance Policy')
    claim_id = fields.Many2one ('hms.insurance.claim', string='Claim')
    insurance_company_id = fields.Many2one ('hms.insurance.company', related='insurance_id.insurance_company_id',
                                            string='Insurance Company', readonly=True, store=True)
    exam_insurance_percentage = fields.Float (related='insurance_id.exam_insurance_percentage',
                                              string="Insured Percentage", readonly=True)
    speciality_id = fields.Many2one ('physician.specialty', related='physician_id.specialty_id', store=True,
                                     string="spécialité")

    def create_invoice(self):
        super (AcsLaboratoryRequest, self).create_invoice ()
        if self.invoice_id and self.insurance_id and (
                self.insurance_id.exam_insurance_limit >= self.invoice_id.amount_total or self.insurance_id.exam_insurance_limit == 0):
            can_be_splited = self.invoice_id.acs_check_auto_spliting_possibility (self.insurance_id)
            _logger.info ("return can_be_splited %s", can_be_splited)
            if can_be_splited:
                split_context = {
                    'active_model': 'account.move',
                    'active_id': self.invoice_id.id,
                    'insurance_id': self.insurance_id.id,
                    'insurance_type': self.insurance_id.exam_insurance_type,
                    'insurance_amount': self.insurance_id.exam_insurance_amount,
                }
                wiz_id = self.env['split.invoice.wizard'].with_context (split_context).create ({
                    'split_selection': 'invoice',
                    'percentage': self.insurance_id.exam_insurance_percentage,
                    'partner_id': self.insurance_company_id.partner_id.id,
                })
                insurance_invoice_id = wiz_id.split_record ()
                insurance_invoice_id.write ({
                    'insurance_id': self.insurance_id.id,
                    'appointment_id': self.appointment_id.id if self.appointment_id else False,
                    'ref': self.name,
                    'invoice_origin': self.name,
                    'hospital_invoice_type': 'laboratory'
                })

                if insurance_invoice_id and self.insurance_id.exam_create_claim:
                    claim_id = self.env['hms.insurance.claim'].create ({
                        'patient_id': self.patient_id.id,
                        'insurance_id': self.insurance_id.id,
                        'claim_for': 'other',
                        'amount_requested': insurance_invoice_id.amount_total,
                    })

                    self.claim_id = claim_id.id
                    insurance_invoice_id.claim_id = claim_id.id
                    self.invoice_id.claim_id = claim_id.id
                # insurance invoice
                product_data = []
                for line in self.line_ids:
                    product_data.append ({
                        'product_id': line.test_id.product_id,
                        'price_unit': line.sale_price * self.insurance_id.exam_insurance_percentage / 100,
                        'quantity': line.quantity,
                    })
                pricelist_context = {}
                if self.pricelist_id:
                    pricelist_context = {'acs_pricelist_id': self.pricelist_id.id}

                invoice = self.with_context (pricelist_context).acs_create_invoice (
                    partner=self.insurance_company_id.partner_id,
                    patient=self.patient_id,
                    product_data=product_data,
                    inv_data={
                        'hospital_invoice_type': 'laboratory',
                        'physician_id': self.physician_id and self.physician_id.id or False})
                self.invoice_id = invoice.id

    @api.onchange ('patient_id')
    def onchange_patient_id(self):
        allow_pharmacy_insurance = self.patient_id.insurance_ids.filtered (lambda x: x.allow_exam_insurance)
        if self.patient_id and allow_pharmacy_insurance:
            insurance = allow_pharmacy_insurance[0]
            self.insurance_id = insurance.id

    def button_requested(self):
        if not self.line_ids:
            raise UserError (_ ('Please add atleast one Laboratory test line before submiting request.'))
        self.name = self.env['ir.sequence'].next_by_code ('acs.laboratory.request')
        if self.is_group_request:
            for line in self.line_ids:
                line.quantity = len (self.group_patient_ids) + 1
        self.state = 'accepted'

    def button_import_patient(self):
        if self.is_group_request:
            return True


class PatientLabTestLine (models.Model):
    _inherit = "laboratory.request.line"

    product_id = fields.Many2one ('product.product', "Service" ,store=True,related='test_id.product_id')


class AcsLabTest (models.Model):
    _inherit = 'acs.lab.test'




