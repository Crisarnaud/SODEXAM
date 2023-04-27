# -*- coding:utf-8 -*-

from odoo import fields, models, api, exceptions, _
from collections import namedtuple
from calendar import monthrange
# from datetime import date
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
import datetime


class RejectRaison(models.TransientModel):
    _name = 'reject.raison'
    _description = 'Reject raison'

    note = fields.Text('Raison du réjet', required=True, tracking=1)

    def action_reject(self):
        acs_laboratory_request = self.env['acs.laboratory.request'].browse(self.env.context.get('active_id'))
        if acs_laboratory_request:
            if acs_laboratory_request.state == 'requested':
                acs_laboratory_request.write({
                    'refuse_raison': self.note
                })
            acs_laboratory_request.return_draft()
