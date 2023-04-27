# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ACSMedicamentGroup(models.Model):
    _name = 'acs.product.kit'
    _order = 'sequence asc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Kit"

    name = fields.Char(string='Group Name', required=True, tracking=True)
    sequence = fields.Integer(default=100)
    acs_kit_line_ids = fields.One2many('acs.product.kit.line', 'acs_kit_id', string='Kit lines')
    description = fields.Text("Description")


class ACSProductKitLine(models.Model):
    _name = 'acs.product.kit.line'
    _order = 'sequence asc'
    _description = "Product Kit Line"

    @api.depends('product_id','product_qty','unit_price')
    def _get_total_price(self):
        for rec in self:
            rec.total_price = rec.unit_price * rec.product_qty

    sequence = fields.Integer(default=100)
    acs_kit_id = fields.Many2one('acs.product.kit', string='Kit', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    name = fields.Char(related='product_id.name', readonly="1")
    uom_id = fields.Many2one(related='product_id.uom_id' , string="Unit of Measure", readonly="1")
    product_qty = fields.Float(string='Quantity', required=True, default=1.0)
    unit_price = fields.Float(related='product_id.list_price', string='Product Price')
    total_price = fields.Float(compute=_get_total_price, string='Total Price')

