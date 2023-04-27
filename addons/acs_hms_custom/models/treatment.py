from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger (__name__)


class HmsTreatment (models.Model):
    _inherit = 'hms.treatment'

    consultation_nas = fields.Boolean ('Est un employé Nas ou Sodexam?', default=False, store=True)

    @api.onchange ('patient_id')
    def onchange_patient_id(self):
        super (HmsTreatment, self).onchange_patient_id ()
        for rec in self:
            if rec.patient_id.corpo_company_id.code_company == 'nas' or rec.patient_id.corpo_company_id.code_company == 'sdx':
                rec.consultation_nas = True
            else:
                rec.consultation_nas = False
        return False

    def create_invoice(self):
        res = super (HmsTreatment, self).create_invoice ()
        lines_to_update = []
        if self.consultation_nas == True:
            for line in self.invoice_id.invoice_line_ids:
                lines_to_update.append ((1, line.id, {'price_unit': self.company_id.price_of_customer_nas_gen}))
            self.invoice_id.update ({'invoice_line_ids': lines_to_update})
        return res



class AcsPatientProcedure (models.Model):
    _inherit = 'acs.patient.procedure'

    consultation_nas = fields.Boolean(related='treatment_id.consultation_nas')

    @api.onchange ('product_id')
    def product_id_change(self):
        super ().product_id_change ()
        for rec in self:
            if rec.treatment_id.consultation_nas == True:
                rec.price_unit = self.company_id.price_of_customer_nas_gen

    # def create_invoice(self):
    #     res = super ().create_invoice ()
    #     lines_to_update = []
    #     if self.treatment_id.consultation_nas == True:
    #         for line in self.invoice_id.invoice_line_ids:
    #             lines_to_update.append ((1, line.id, {'price_unit': self.company_id.price_of_customer_nas_gen}))
    #         self.invoice_id.update ({'invoice_line_ids': lines_to_update})
    #     return res
