# -*- coding:utf-8 -*-

from odoo import api, fields, _, models
from dateutil import relativedelta
from odoo.exceptions import UserError, Warning


class HrHolidaysRecovery(models.Model):
    _name = "hr.holidays.recovery"
    _description = "HR Holidays Recovery"
    _rec_name = "employee_id"

    employee_id = fields.Many2one('hr.employee', 'Employé', required=True)
    holidays_id = fields.Many2one('hr.leave', 'Congé', required=True, domain="[('employee_id', '=', employee_id),"
                                                                             "('state', '=', 'validate'),"
                                                                             "('reprise','=', False)]")
    recovery_date = fields.Date("Date de reprise", required=True)
    recovery_hour = fields.Char("Heure de réprise", required=True, default='07H30')
    number_of_holidays = fields.Float("Nombre de jours", required=True, readonly=True,
                                      related="holidays_id.number_of_days")
    direction_id = fields.Many2one("hr.department", "Direction", related="employee_id.direction_id")
    department_id = fields.Many2one("hr.department", "Departement", related="employee_id.department_id")
    service_id = fields.Many2one("hr.department", "Service", related="employee_id.service_id")
    state = fields.Selection([('draft', "brouillon"), ("service", "Chef de service / CA"),
                              ("department", "Chef de departement"), ('direction', "Directeur"),
                              ('drh', "Directeur des RH"),
                              ('done', "Validé"), ('cancel', "Annulé")], "Etat", default="draft")
    validator_id = fields.Many2one('hr.employee', 'Validateur', required=False, related='employee_id.parent_id')
    company_id = fields.Many2one('res.company', 'Société', default=1)

    @api.onchange('holidays_id')
    def onChangeHoliday(self):
        self.recovery_date = self.holidays_id.request_date_to + relativedelta.relativedelta(days=+1) \
            if self.holidays_id.request_date_to else False

    def action_submit(self):
        for rec in self:
            rec.state == 'done'

    def action_chief_service(self):
        for data in self:
            data.state = 'department'

    def action_chief_direction(self):
        for data in self:
            data.state = 'drh'

    def action_done(self):
        for data in self:
            data.state = 'done'
            data.holidays_id.reprise = True

    def action_cancel(self):
        for data in self:
            data.state = 'cancel'

    def action_to_draft(self):
        for data in self:
            if data.employee_id.type_employee in ('employee', 'service_chief'):
                data.state = 'service'
            elif data.employee_id.type_employee == 'department_chief':
                data.state = 'department'
            elif data.employee_id.type_employee == 'direction':
                data.state = 'drh'
            else:
                return True


class HrcnceReportHolidayRecovery(models.AbstractModel):
    _name = 'report.hr_holiday_custom.report_hr_holidays_recovery'
    _description = 'Attestation de reprise de service'

    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.holidays.recovery'].browse(docids)
        if docs.state != 'done':
            raise Warning("Vous ne pouvez imprimer la fiche de reprise de congé que si elle est validée")
        else:
            return {
                'doc_ids': docs.ids,
                'doc_model': 'hr.holidays.recovery',
                'docs': docs,
            }
