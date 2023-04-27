# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning,ValidationError
import datetime
import xlrd
import base64
import logging

_logger = logging.getLogger (__name__)


class AcsLaboratoryAeroRequestWizard (models.Model):
    _name = 'acs.laboratory.aero.request.wizard'

    def default_request_id(self):
        active_ids = self.env.context.get ("active_ids")
        if active_ids:
            return self.env["acs.laboratory.request"].browse (active_ids[0])
        return self.env["acs.laboratory.request"]

    csv_file = fields.Binary (string='', required=True)
    request_id = fields.Many2one ('acs.laboratory.request', default=default_request_id)

    def compute_data(self):
        res = []
        list_patient = []
        try:
            wb = xlrd.open_workbook (file_contents=base64.b64decode (self.csv_file))
        except FileNotFoundError:
            raise UserError ('No such file or directory found')
        sheet = wb.sheet_by_index (0)
        for row in range (sheet.nrows):
            if row >= 1:
                row_vals = sheet.row_values (row)
                xl_date = row_vals[4]
                datetime_date = xlrd.xldate_as_datetime (xl_date, 0)
                date_object = datetime_date.date ()
                vals = {
                    'name': row_vals[0],
                    'last_name': row_vals[0],
                    'first_name': row_vals[1],
                    'mobile': row_vals[2],
                    'gender': row_vals[3],
                    'birthday': (date_object).strftime ('%Y-%m-%d'),
                    'aeronautical_customer': row_vals[5],
                }
                patients = self.env['hms.patient'].search([])
                for patient in patients:
                    list_patient.append(patient.name)
                    list_patient.append(patient.birthday)
                    list_patient.append(patient.mobile)

                if str(row_vals[0]) not in list_patient and str(row_vals[2]) not in list_patient and str(row_vals[4]) not in list_patient:
                    res.append (vals)
        self.request_id.group_patient_ids = self.request_id.group_patient_ids.create(res)

