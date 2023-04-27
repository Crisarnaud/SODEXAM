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


class Physician (models.Model):
    _inherit = 'hms.physician'

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get ('code', '/') == '/':
                values['code'] = self.env['ir.sequence'].next_by_code ('hms.physician')
            if values.get ('email'):
                values['login'] = values.get ('email')
            else:
                values['login'] = values.get ('name')
            # ACS: It creates issue in physican creation
            if values.get ('user_ids'):
                values.pop ('user_ids')
            users = super (Physician, self).create (vals_list)
            for user in users:
                user.groups_id = [(4, self.env.ref ('acs_hms_custom.make_invisible').id)]
        return users



