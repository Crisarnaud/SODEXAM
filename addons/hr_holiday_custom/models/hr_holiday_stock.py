from odoo import api, fields, models, _
from datetime import date


class HrStockHoliday(models.Model):
    _name = "last.holiday"
    _description = "stock des congés précédents"

    date_start_last_holiday_previsional = fields.Date('Date prévsionnelle de départ dernier congé',
                                                      compute='_get_date_start_last_holiday_prev')
    date_return_last_holiday_previsional = fields.Date('Date prévsionnelle retour dernier congé',
                                                       compute='_get_date_return_last_holiday_prev')
    date_return_last_holiday = fields.Date('Date retour dernier congé')
    number_day_last_holiday = fields.Char('Durée dernier congé', compute='_get_duree_last_holiday_prev')
    employee_id = fields.Many2one('hr.employee', 'Employe')

    def _get_date_start_last_holiday_prev(self):
        date_leave = []
        employee = self.env['hr.employee'].search([('id', '=', self.employee_id.id)])
        date_leave.append(employee.estimed_date_leave)
        for i in date_leave:
            self.date_start_last_holiday_previsional = i
        return self.date_start_last_holiday_previsional

    def _get_date_return_last_holiday_prev(self):
        employee = self.env['hr.employee'].search([('id', '=', self.employee_id.id)])
        self.date_return_last_holiday_previsional = employee.estimated_date_return_leave
        return self.date_return_last_holiday_previsional

    def _get_date_return_last_holiday(self):
        employee = self.env['hr.employee'].search([('id', '=', self.employee_id.id)])
        self.date_start_last_holiday_previsional = employee.estimated_date_return_leave
        return self.date_start_last_holiday_previsional

    def _get_duree_last_holiday_prev(self):
        employee = self.env['hr.employee'].search([('id', '=', self.employee_id.id)])
        self.number_day_last_holiday = employee.number_days_estimed_holidays
        return self.date_start_last_holiday_previsional


class HrSavePlanningHoliday(models.Model):
    _name = 'save.planning.holiday'
    _description = "Sauvegarde du planning congé"

    estimed_date_leave = fields.Date('Date prévsionnelle de départ en congés', )
    estimated_date_return_leave = fields.Date('Date prévsionnelle de retour de congés', )
    date_return_last_holidays = fields.Date('Date de retour congés')
    number_days_estimed_holidays = fields.Char('Nombre de jours de congés estimés')
    employee_id = fields.Many2one('hr.employee', 'Employe')


class HrSaveStockHoliday(models.Model):
    _name = 'save.stock.holiday'
    _description = "Sauvegarde des stocks congés"

    name = fields.Char('Stock congé')
    number_days = fields.Integer("Nombre de jours")
    employee_id = fields.Many2one('hr.employee', 'Employé')
