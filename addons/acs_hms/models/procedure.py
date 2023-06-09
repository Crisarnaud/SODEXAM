# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class AcsPatientProcedure(models.Model):
    _name="acs.patient.procedure"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin']
    _description = "Patient Procedure"
    _order = "id desc"

    STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}

    name = fields.Char(string="Name", states=STATES, tracking=True)
    patient_id = fields.Many2one('hms.patient', string='Patient', required=True, states=STATES, tracking=True)
    product_id = fields.Many2one('product.product', string='Procedure', 
        change_default=True, ondelete='restrict', states=STATES, required=True)
    price_unit = fields.Float("Price", states=STATES)
    invoice_id = fields.Many2one('account.move', string='Invoice', ondelete='cascade', states=STATES, copy=False)
    physician_id = fields.Many2one('hms.physician', ondelete='restrict', string='Physician', 
        index=True, states=STATES)
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('cancel', 'Canceled'),
    ], string='State', default='scheduled', tracking=True)
    company_id = fields.Many2one('res.company', ondelete='restrict', states=STATES,
        string='Hospital', default=lambda self: self.env.user.company_id.id)
    date = fields.Datetime("Date")
    diseas_id = fields.Many2one('hms.diseases', 'Disease', states=STATES)
    description = fields.Text(string="Description")
    treatment_id = fields.Many2one('hms.treatment', 'Treatment', states=STATES)
    appointment_ids = fields.Many2many('hms.appointment', 'acs_appointment_procedure_rel', 'appointment_id', 'procedure_id', 'Appointments', states=STATES)
    department_id = fields.Many2one('hr.department', ondelete='restrict', 
        domain=[('patient_department', '=', True)], string='Department', tracking=True, states=STATES)
    department_type = fields.Selection(related='department_id.department_type', string="Appointment Department", store=True)

    consumable_line_ids = fields.One2many('hms.consumable.line', 'procedure_id',
        string='Consumable Line', states=STATES, copy=False)
    acs_kit_id = fields.Many2one('acs.product.kit', string='Kit', states=STATES)
    acs_kit_qty = fields.Integer("Kit Qty", states=STATES, default=1)

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            self.name = self.product_id.name_get()[0][1]
            self.price_unit = self.product_id.list_price

    def action_running(self):
        self.state = 'running'

    def action_schedule(self):
        self.state = 'scheduled'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def unlink(self):
        for rec in self:
            if rec.state not in ['cancel']:
                raise UserError(_('Record can be deleted only in Canceled state.'))
        return super(AcsPatientProcedure, self).unlink()
 
    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('acs.patient.procedure') or 'New Procedure'
        return super(AcsPatientProcedure, self).create(values)


    def action_create_invoice(self):
        product_id = self.product_id
        if not product_id:
            raise UserError(_("Please Set Product first."))
        product_data = [{
            'product_id': product_id, 
            'price_unit': self.price_unit
        }]

        for consumable in self.consumable_line_ids:
            product_data.append({
                'product_id': consumable.product_id,
                'quantity': consumable.qty,
            })

        if self.consumable_line_ids:
            self.consume_procedure_material()

        inv_data = {
            'physician_id': self.physician_id and self.physician_id.id or False,
        }
        invoice = self.acs_create_invoice(partner=self.patient_id.partner_id, patient=self.patient_id, product_data=product_data, inv_data=inv_data)
        self.invoice_id = invoice.id

    def consume_procedure_material(self):
        for rec in self:
            if not rec.company_id.appointment_usage_location_id:
                raise UserError(_('Please define a stock usage location where the consumables will be used.'))
            if not rec.company_id.appointment_stock_location_id:
                raise UserError(_('Please define a stock location from where the consumables will be taken.'))

            dest_location_id  = rec.company_id.appointment_usage_location_id.id
            source_location_id  = rec.company_id.appointment_stock_location_id.id
            for line in rec.consumable_line_ids.filtered(lambda s: not s.move_id):
                move = self.consume_material(source_location_id, dest_location_id,
                    {
                        'product': line.product_id,
                        'qty': line.qty,
                    })
                move.procedure_id = rec.id
                line.move_id = move.id

    def view_invoice(self):
        invoices = self.mapped('invoice_id')
        action = self.acs_action_view_invoice(invoices)
        return action

    def action_show_details(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_procedure")
        action['context'] = {'default_patient_id': self.id}
        action['res_id'] = self.id
        action['views'] = [(self.env.ref('acs_hms.view_acs_patient_procedure_form').id, 'form')]
        action['target'] = 'new'
        return action

    def get_acs_kit_lines(self):
        if not self.acs_kit_id:
            raise UserError("Please Select Kit first.")

        lines = []
        for line in self.acs_kit_id.acs_kit_line_ids:
            lines.append((0,0,{
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'qty': line.product_qty * self.acs_kit_qty,
            }))
        self.consumable_line_ids = lines


class StockMove(models.Model):
    _inherit = "stock.move"

    procedure_id = fields.Many2one('acs.patient.procedure', ondelete="cascade", string="Procedure")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:   