# -*- coding:utf-8 -*-

import logging
from odoo import api, fields, _, models
from dateutil import relativedelta


_logger = logging.getLogger(__name__)


class HrHolidaysProvision(models.Model):
    _name = "hr.holidays.provision"
    _description = "Provision de conges"

    name = fields.Char("Libellé", required=True, size=225)
    type = fields.Selection([('employee', 'Par employé'), ('all', 'Tous les employés')], 'Type de calcul',
                            default="all")
    date_end = fields.Date("Date de fin", required=True)
    employee_id = fields.Many2one("hr.employee", 'Employé', required=False)
    line_ids = fields.One2many('hr.holidays.provision.line', 'hr_provision_id', 'Lignes')
    company_id = fields.Many2one('res.company', "Société", default=lambda self: self.env.user.company_id.id)

    def get_extra_leave_days(self, id_employee):
        employee_rc = self.env['hr.employee'].search([('id', '=', id_employee)])
        if employee_rc:
            nbr_days = 0
            anc = employee_rc.seniority_employee
            if 5 <= anc < 10:
                nbr_days += 1
            elif 10 <= anc < 15:
                nbr_days += 2
            elif 15 <= anc < 20:
                nbr_days += 3
            elif 20 <= anc < 25:
                nbr_days += 5
            elif 25 <= anc < 30:
                nbr_days += 7
            elif anc >= 30:
                nbr_days += 8
            if employee_rc.gender == 'female':
                if employee_rc.age < 21:
                    nbr_days += 2 * employee_rc.children
                else:
                    if employee_rc.children >= 4:
                        nbr_days += 2 * (employee_rc.children - 3)
        return nbr_days

    def compute(self):
        for provision in self:
            provision.line_ids.unlink()
            res = []

            if provision.type == 'employee':
                extra_days = self.get_extra_leave_days(provision.employee_id.id)
                facteur = provision.company_id.number_holidays_locaux if provision.employee_id.nature_employe == 'local' \
                    else provision.company_id.number_holidays_expat
                tmp = provision.date_end - provision.employee_id.date_return_last_holidays
                number_holidays = extra_days + round(tmp.days * 12 / 360) * facteur
                number_holidays = round(number_holidays + number_holidays / 6)
                vals = {
                    "employee_id": provision.employee_id.id,
                    "date_start": self.employee_id.date_return_last_holidays,
                    "date_end": provision.date_end,
                    "number_holidays": number_holidays
                }
                res.append(vals)
            else:
                employees = self.env['hr.employee'].search([])
                if employees:
                    for emp in employees:
                        extra_days = self.get_extra_leave_days(emp.id)
                        facteur = provision.company_id.number_holidays_locaux if emp.nature_employe == 'local' \
                            else provision.company_id.number_holidays_expat
                        if emp.date_return_last_holidays:
                            tmp = provision.date_end - emp.date_return_last_holidays
                            number_holidays = extra_days + round(tmp.days * 12 / 360) * facteur
                            number_holidays = round(number_holidays + number_holidays / 6)
                            vals = {
                                "employee_id": emp.id,
                                "date_start": emp.date_return_last_holidays,
                                "date_end": provision.date_end,
                                "number_holidays": number_holidays,

                                'hr_provision_id': self.id,
                            }
                            res.append(vals)
                self.env['hr.holidays.provision.line'].create(vals)


class HrHolidaysProvisinLine(models.Model):
    _name = "hr.holidays.provision.line"
    _description = "Ligne de provision conges"

    employee_id = fields.Many2one("hr.employee", required=True)
    date_start = fields.Date("Date de retour congés")
    date_end = fields.Date("Date de fin", required=True)
    number_holidays = fields.Float("Nombre de jours de congés", digits=(10, 2))
    hr_provision_id = fields.Many2one("hr.holidays.provision", "Parent", required=False)