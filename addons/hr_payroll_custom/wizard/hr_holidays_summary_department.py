# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HolidaysSummaryDept(models.TransientModel):
    _inherit = 'hr.holidays.summary.employee'

    depts = fields.Many2many('hr.department', 'summary_dept_rel', 'sum_id', 'dept_id', string='Department(s)')
    type = fields.Many2one('hr.leave.type', "Type")
    date_to = fields.Date(string='À', required=False)

    def print_report_holiday(self):

        if self.date_to:
            leaves = self.env['hr.leave'].search([('state', '=', 'validate'),
                                                  ('request_date_from', '>=', self.date_from),
                                                  ('request_date_to', '<=', self.date_to)])
            datas = {
                'ids': [],
                'model': 'hr.leave',
                'form': leaves
            }

            return self.env.ref('hr_holidays_extension.report_agent_on_leave').report_action(self, data=datas)
