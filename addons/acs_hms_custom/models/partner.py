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



class ResPartner(models.Model):
    _inherit = 'res.partner'

    code_company = fields.Char("Code compagnie")