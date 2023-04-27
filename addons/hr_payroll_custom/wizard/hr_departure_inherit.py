# -*- coding:utf-8 -*-

import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class AccountMoveTemplate(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    employee_id = fields.Many2one(
        'hr.employee', store=True, string='Employee', required=True,
        default=lambda self: self.env.context.get('active_id'),
    )
    departure_reason_id = fields.Many2one('hr.employee.motif.cloture', 'Motif du départ',
                                          related='employee_id.motif_fin_contract_id', store=True)
    date_departure = fields.Date('Date de fin de contrat', related='employee_id.end_date')
