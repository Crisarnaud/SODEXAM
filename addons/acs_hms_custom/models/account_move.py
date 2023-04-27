from datetime import datetime

from odoo import fields, models, api,_
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger(__name__)


class AccountMove (models.Model):
    _inherit = 'account.move'

