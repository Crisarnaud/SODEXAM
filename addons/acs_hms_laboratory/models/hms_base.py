# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Hospitalization(models.Model):
    _inherit = "acs.hospitalization"

    def _rec_count(self):
        rec = super(Hospitalization, self)._rec_count()
        for rec in self:
            rec.request_count = len(rec.request_ids)
            rec.test_count = len(rec.test_ids)

    request_ids = fields.One2many('acs.laboratory.request', 'hospitalization_id', string='Lab Requests')
    test_ids = fields.One2many('patient.laboratory.test', 'hospitalization_id', string='Tests')
    request_count = fields.Integer(compute='_rec_count', string='# Lab Requests')
    test_count = fields.Integer(compute='_rec_count', string='# Lab Tests')

    def action_lab_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.hms_action_lab_test_request")
        action['domain'] = [('id','in',self.request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_hospitalization_id': self.id}
        action['views'] = [(self.env.ref('acs_laboratory.patient_laboratory_test_request_form').id, 'form')]
        return action

    def action_lab_requests(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.hms_action_lab_test_request")
        action['domain'] = [('id','in',self.request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_hospitalization_id': self.id}
        return action

    def action_view_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.action_lab_result")
        action['domain'] = [('id','in',self.test_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_hospitalization_id': self.id}
        return action

    def acs_hospitalization_invoices(self, invoice_id):
        res = super(Hospitalization, self).acs_hospitalization_invoices(invoice_id)
        #Lab request invoicing
        request_ids = self.mapped('request_ids').filtered(lambda req: req.state=='to_invoice' and not req.invoice_id)
        if request_ids:
            self.acs_create_invoice_line({'name': _("Laboratory Charges")}, invoice_id)
            for lab_request in request_ids:
                pricelist_id = lab_request.pricelist_id and lab_request.pricelist_id.id or False
                for line in lab_request.line_ids:
                    product_data = {
                        'product_id': line.test_id.product_id,
                        'price_unit': line.sale_price,
                        'quantity': line.quantity,
                    }
                    self.with_context(acs_pricelist_id=pricelist_id).acs_create_invoice_line(product_data, invoice_id)
                lab_request.invoice_id = invoice_id.id
                #ACS: it is possible that on hospitalization done we can mark record as done or we can do it on invoice validation also.
                lab_request.button_done()
        return res


class ACSAppointment(models.Model):
    _inherit='hms.appointment'

    def _rec_count(self):
        for rec in self:
            rec.request_count = len(rec.lab_request_ids)
            rec.test_count = len(rec.test_ids)

    test_ids = fields.One2many('patient.laboratory.test', 'appointment_id', string='Lab Tests')
    lab_request_ids = fields.One2many('acs.laboratory.request', 'appointment_id', string='Lab Requests')
    request_count = fields.Integer(compute='_rec_count', string='# Lab Requests')
    test_count = fields.Integer(compute='_rec_count', string='# Lab Tests')

    def action_lab_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.hms_action_lab_test_request")
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_appointment_id': self.id}
        action['views'] = [(self.env.ref('acs_laboratory.patient_laboratory_test_request_form').id, 'form')]
        return action

    def action_view_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.action_lab_result")
        action['domain'] = [('id','in',self.test_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_appointment_id': self.id}
        return action

    def action_view_lab_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.hms_action_lab_test_request")
        action['domain'] = [('id','in',self.lab_request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_appointment_id': self.id}
        return action


class Treatment(models.Model):
    _inherit = "hms.treatment"

    def _lab_rec_count(self):
        for rec in self:
            rec.request_count = len(rec.request_ids)
            rec.test_count = len(rec.test_ids)

    request_ids = fields.One2many('acs.laboratory.request', 'treatment_id', string='Lab Requests')
    test_ids = fields.One2many('patient.laboratory.test', 'treatment_id', string='Tests')
    request_count = fields.Integer(compute='_lab_rec_count', string='# Lab Requests')
    test_count = fields.Integer(compute='_lab_rec_count', string='# Lab Tests')

    def action_lab_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.hms_action_lab_test_request")
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_treatment_id': self.id}
        action['views'] = [(self.env.ref('acs_laboratory.patient_laboratory_test_request_form').id, 'form')]
        return action

    def action_lab_requests(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.hms_action_lab_test_request")
        action['domain'] = [('id','in',self.request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_treatment_id': self.id}
        return action

    def action_view_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.action_lab_result")
        action['domain'] = [('id','in',self.test_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_treatment_id': self.id}
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: