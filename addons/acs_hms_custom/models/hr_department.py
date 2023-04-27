from datetime import datetime

from odoo import fields, models, api,_
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger(__name__)

class HrDepartment (models.Model):
    _inherit = 'hr.department'

    patient_department = fields.Boolean("Patient Department", default=False)


