# -*- coding:utf-8 -*-

from odoo import api, fields, _, models
from dateutil.relativedelta import relativedelta
import babel
from datetime import date, datetime, time


class HrPayrollHolidaysProvison(models.Model):
    _name = "hr.payroll.holidays_provision"
    _description = "Hr Holidays payroll provision"

    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))


class HrPayrollHolidaysProvisonLine(models.Model):
    _name = "hr.payroll.holidays_provision_line"
    _description = "Hr Holidays payroll provision"

    employee_id = fields.Many2one("hr.employee", "Employé", required=True)
    brut_imposable_mensuel = fields.Float("Brut imposable mensuel")
    cumul_net = fields.Float("Cumul net")
    cumul_brut_imposable_holidays = fields.Float("Cumul brut imosable de dernier congé")
    cumul_worked_days = fields.Float("Cumul jours de présence déouis dernier congé")
    holidays_acquired = fields.Float("Nombre de jours acquis")
    holidays_calendar_acquired = fields.Float("Nombre de jours ouvrables de congés")
    salaire_moyen_mensuel = fields.Float("Salaire moyen mensuel")
    salaire_moyen_daily = fields.Float("Salaire moyen journalier")
    amount_holidays_acquired = fields.Float("Montant congés acquis")
    amount_cnps = fields.Float("CNPS")
    amount_its = fields.Float('ITS')
    amount_fdfp = fields.Float("FDFP")
    amout_total = fields.Float("Total")
