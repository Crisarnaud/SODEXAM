# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from lxml import etree


class ACSPatient (models.Model):
    _inherit = "hms.patient"

    aeronautical_customer = fields.Boolean ("Client aéronautique")


class HrDepartment (models.Model):
    _inherit = "hr.department"

    department_type = fields.Selection (selection_add=[('aero', 'Aeronautics')])


class ACSAppointment (models.Model):
    _inherit = 'hms.appointment'

    aeronautical_customer = fields.Boolean (related="patient_id.aeronautical_customer", string='Client aéronautique',
                                            readonly=True)

    @api.onchange ('patient_id')
    def onchange_patient_id(self):
        super (ACSAppointment, self).onchange_patient_id ()
        if self.aeronautical_customer == True:
            self.consultation_nas = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super (ACSAppointment, self).fields_view_get (view_id, view_type, toolbar=toolbar, submenu=submenu)
        context = self._context
        if context.get ('acs_department_type') == 'aero':
            doc = etree.XML (result['arch'])
            node = doc.xpath ("//field[@name='patient_id']")[0]
            node.set ('domain', "[('aeronautical_customer','=',True)]")
            result['arch'] = etree.tostring (doc, encoding='unicode')
        return result
