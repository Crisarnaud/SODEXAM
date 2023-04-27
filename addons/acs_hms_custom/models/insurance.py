from datetime import datetime

from odoo import fields, models, api,_
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger(__name__)


class HmsAppointment (models.Model):
    _inherit = 'hms.patient.insurance'

    allow_exam_insurance = fields.Boolean(string="Examen assuré", default=False,store=True)
    exam_insurance_type = fields.Selection([
        ('percentage', 'Pourcentage'),
        ('fix', 'prix fixe')], "Type d'assurance examen", default='percentage', required=True,store=True)
    exam_insurance_amount = fields.Float(string="Co paiement", help="The patient should pay specific amount 50QR")
    exam_insurance_percentage = fields.Float(string="Pourcentage d'examen assuré",store=True)
    exam_insurance_limit = fields.Float(string="Limite d'assurance d'examen", store=True)
    exam_create_claim = fields.Boolean(string="Créer une réclamation d'examen", default=False,store=True)

    @api.onchange('insurance_plan_id')
    def onchange_insurance_plan(self):
        res = super (HmsAppointment, self).onchange_insurance_plan()
        if self.insurance_plan_id:
            self.allow_exam_insurance = self.allow_exam_insurance
            self.exam_insurance_type = self.exam_insurance_type
            self.exam_insurance_amount = self.exam_insurance_amount
            self.exam_insurance_percentage = self.exam_insurance_percentage
            self.exam_insurance_limit = self.exam_insurance_limit
            self.exam_create_claim = self.exam_create_claim
        return res

class InsuranceClaim (models.Model):
    _inherit = 'hms.insurance.claim'

class AcsClaimSheet (models.Model):
    _inherit = 'acs.claim.sheet'

    amount_total = fields.Float (compute="_amount_all", string="Total", store=True)

    def get_data(self):
        self.claim_line_ids.write ({'claim_sheet_id': False})
        domain = [
            ('insurance_company_id', '=', self.insurance_company_id.id),
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('claim_sheet_id', '=', False),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'draft')]
        _logger.info('nous sommes dans la fonction get data %s', domain)
        claim_lines = self.env['account.move'].search (domain)
        claim_lines.write ({'claim_sheet_id': self.id})
