from odoo import fields, models, api,_
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger(__name__)

class product_template(models.Model):
    _inherit = "product.template"

    type = fields.Selection([
        ('consu', 'Consommable'),
        ('service', 'Service'),
        ('product', 'Article stockable'),
    ], string="Type d'article", copy=False, default='service')
    purchase_ok = fields.Boolean(default=False)