from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger (__name__)


class AcsCommission (models.Model):
    _inherit = 'acs.commission'

    invoice_line_id = fields.Many2one ('account.move.line', 'Payment Invoice Line',
                                       domain="[('move_id', '=', invoice_id)]")


class AcoountMove (models.Model):
    _inherit = "account.move"


class AcsLaboratoryRequest (models.Model):
    _inherit = "acs.laboratory.request"

    def create_invoice(self):
        res = super (AcsLaboratoryRequest, self).create_invoice ()
        move = self.env['account.move'].search ([('invoice_origin', '!=', str (self.name))])
        for test in move:
            test.update({'commission_partner_ids': [(4, self.physician_id.partner_id.id)]})
        for rec in self:
            rec.invoice_id.onchange_total_amount ()
            rec.invoice_id.onchange_ref_physician ()
            rec.invoice_id.onchange_physician ()

        return res
