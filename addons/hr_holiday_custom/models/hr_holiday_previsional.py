# -*- coding:utf-8 -*-

from odoo import fields, models, api
from collections import namedtuple
from calendar import monthrange
from datetime import datetime
from dateutil.relativedelta import relativedelta
import datetime


class hr_holidays_previsional(models.Model):
    _name = 'hr.previsional.leave'
    _description = "hr previsional leave"

    @api.depends('departure_date')
    def _function_date(self):
        for dates in self:
            if dates.departure_date:
                dates.previsional_departure_date = dates.departure_date + relativedelta(years=1)
                dates.return_date = dates.previsional_departure_date + datetime.timedelta(days=33)
                dates.fifteen_days_after_departure = dates.previsional_departure_date - datetime.timedelta(days=15)

    employee_id = fields.Many2one('hr.employee', 'Nom de l`employé', required=True)
    departure_date = fields.Date('Date départ', related='employee_id.date_return_last_holidays')
    previsional_departure_date = fields.Date('Date départ prévisionnel', compute=_function_date, store=True)
    return_date = fields.Date('Date de retour prévisionnel', compute=_function_date, store=True)
    fifteen_days_after_departure = fields.Date('Notification à récevoir le:', compute=_function_date, store=True)
    employee_email = fields.Char('email', related='employee_id.work_email')
    numbers_of_days = fields.Float('Nombre de jours', related='employee_id.leaves_count')
