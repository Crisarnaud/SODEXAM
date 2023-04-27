# -*- coding:utf-8 -*-
from psycopg2._psycopg import cursor

from odoo import api, models, fields, _


class HrHolidaysWizard(models.TransientModel):
    _name = 'hr.holidays.refuse.wizard'
    _description = "Assistant de refus de vacances"

    motif_refus = fields.Text('Motif de refus', required=True)

    def action_refus(self):
        holidays = self.env['hr.leave'].browse(self.env.context.get('active_id'))
        current_state = holidays.state
        if current_state == 'service':
            holidays.write({'state': 'draft', 'refuse': 'oui'})
            holidays.send_notification('email_template_refuse_request')
        elif current_state == 'department':
            if holidays.employee_id.service_id:
                holidays.write({'state': 'service', 'refuse': 'oui'})
                holidays.send_notification('email_template_refuse_request')
            holidays.write({'state': 'draft'})
            holidays.send_notification('email_template_refuse_request')
        elif current_state == 'direction':
            if holidays.employee_id.department_id:
                holidays.write({'state': 'department', 'refuse': 'oui'})
                holidays.send_notification('email_template_refuse_request')
            if holidays.employee_id.service_id:
                holidays.write({'state': 'service'})
                holidays.send_notification('email_template_refuse_request')
            holidays.write({'state': 'draft'})
            holidays.send_notification('email_template_refuse_request')
        elif current_state == 'service_admin':
            if holidays.employee_id.direction_id:
                holidays.write({'state': 'direction', 'refuse': 'oui'})
                holidays.send_notification('email_template_refuse_request')
            if holidays.employee_id.department_id:
                holidays.write({'state': 'department'})
                holidays.send_notification('email_template_refuse_request')
            if holidays.employee_id.service_id:
                holidays.write({'state': 'service'})
                holidays.send_notification('email_template_refuse_request')
            holidays.write({'state': 'draft'})
            holidays.send_notification('email_template_refuse_request')
        else:
            return False

        holidays.write({
            'motif_refus': self.motif_refus
        })
