# -*- coding:utf-8 -*-

import logging
from odoo import api, fields, _, models
from odoo.exceptions import ValidationError, UserError
from dateutil import relativedelta
from datetime import date

_logger = logging.getLogger(__name__)


class HrHolidaysPlanning(models.Model):
    _name = "hr.holiday.planning"
    _description = "HR Holidays Planning"

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char("Libellé", required=True, size=225, default="Planning personnel de congé")
    employee_id = fields.Many2one("hr.employee", 'Employé', required=False, default=_default_employee)
    date_from = fields.Date("Début", required=True)
    date_end = fields.Date("Date de fin", required=True)
    number_of_days = fields.Float("Nombre jours")
    date_first_alert = fields.Date("Date première alerte")
    date_second_alert = fields.Date("Date deuxième alerte")
    # number_of_days_availibillity = fields.Float("Nombre de jours disponible")
    holiday_type = fields.Many2one('hr.leave.type', "Type",
                                   default=lambda self: self.env['hr.leave.type'].search(
                                       [('code', '=', 'CONG')], limit=1).id)
    company_id = fields.Many2one('res.company', "Société", default=lambda self: self.env.user.company_id.id)
    direction_id = fields.Many2one("hr.department", "Direction", related="employee_id.direction_id")
    department_id = fields.Many2one("hr.department", "Departement", related="employee_id.department_id")
    service_id = fields.Many2one("hr.department", "Service", related="employee_id.service_id")
    state = fields.Selection(
        [('draft', 'Brouillon'), ('service', 'Chef de service/ CA'), ('department', 'Chef de departement'),
         ('direction', 'Directeur'), ('service_admin', 'Service administratif'),
         ('done', 'Validé'), ('cancel', 'Annulé')], string='Statut', default='draft')

    @api.onchange('date_from', 'date_end')
    @api.depends('date_from', 'date_end')
    def _get_number_of_days(self):
        if self.date_from and self.date_end:
            date_end = fields.Datetime.from_string(self.date_end)
            date_from = fields.Datetime.from_string(self.date_from)
            leave_rec = self.env['hr.leave'].search([], limit=1)
            number_days = (date_end - date_from).days
            self.number_of_days = 1 + number_days
        else:
            self.number_of_days = 0

    def action_submit(self):
        if self.employee_id.type_employee == 'employee':

            if self.service_id:
                self.state = 'service'
                # self.send_notification('email_template_validate_real_planning')
            elif not self.service_id and self.department_id:
                self.state = 'department'
                # self.send_notification('email_template_validate_real_planning')
            elif not self.service_id and not self.department_id and self.direction_id:
                self.state = 'direction'
                # self.send_notification('email_template_validate_real_planning')
            else:
                self.state = 'service_admin'
                # self.send_notification('email_template_validate_real_planning')

        elif self.employee_id.type_employee == 'service_chief':

            if self.department_id:
                self.state = 'department'
                # self.send_notification('email_template_validate_real_planning')
            elif not self.department_id and self.direction_id:
                self.state = 'direction'
                # self.send_notification('email_template_validate_real_planning')
            else:
                self.state = 'service_admin'
                # self.send_notification('email_template_validate_real_planning')

        elif self.employee_id.type_employee == 'department_chief':

            if self.direction_id:
                self.state = 'direction'
                # self.send_notification('email_template_validate_real_planning')
            else:
                self.state = 'service_admin'
                # self.send_notification('email_template_validate_real_planning')

        elif self.employee_id.type_employee == 'director':
            self.state = 'service_admin'
            # self.send_notification('email_template_validate_real_planning')
        else:
            raise UserError(_('The agent is not assigned to a service, a department, or a direction. The request '
                              'will not be validated.'))

    def action_chief_department(self):
        if self.department_id:
            self.state = 'department'
            # self.send_notification('email_template_validate_real_planning')
        elif not self.department_id and self.direction_id:
            self.state = 'direction'
            # self.send_notification('email_template_validate_real_planning')
        else:
            self.state = 'service_admin'
            # self.send_notification('email_template_validate_real_planning')

    def action_director(self):
        if self.direction_id:
            self.state = 'direction'
            # self.send_notification('email_template_validate_real_planning')
        else:
            self.state = 'service_admin'
            # self.send_notification('email_template_validate_real_planning')

    def action_administrative_department(self):
        self.state = 'service_admin'
        self.send_notification('email_template_validate_real_planning')

    def action_cancel(self):
        self.state = 'cancel'
        self.send_notification('email_template_validate_real_planning')

    def action_rejected(self):
        self.state = 'draft'
        self.send_notification('email_template_real_planning')

    def action_validate(self):
        self.state = 'done'
        self.send_notification('email_template_real_planning')

    def action_to_draft(self):
        self.state = 'draft'

    @api.constrains('date_from', 'date_end', 'employee_id')
    def _check_contraints(self):
        if self.date_from > self.date_end:
            raise ValidationError(_("La date de fin doit toujours être supérieure à la date de début"))
        today = date.today()
        if self.date_from.year != today.year or self.date_end.year != today.year:
            raise ValidationError(
                _("Vous ne pouvez prendre des congés prévisionnels que pour cette année %s") % today.year)
        leave_taken = self.get_number_days_taken(self.employee_id.id)
        if leave_taken > self.employee_id.stock_total_holiday:
            raise ValidationError(_("Impossible d'enregistrer cette opération car le nombre de jours demandés doit "
                                    "être inférieur ou égal au nombre de jours possible"))

    def send_notification(self, email_id):
        template_id = self.env['ir.model.data'].get_object_reference('hr_holiday_custom', email_id)
        try:
            mail_templ = self.env['mail.template'].browse(template_id[1])
            result = mail_templ.send_mail(res_id=self.id, force_send=True)
            return True
        except:
            return False

    def get_number_days_taken(self, id_employee):
        num_day = 0
        if id_employee:
            today = date.today()
            first_date = date(today.year, 1, 1)
            planning_rc = self.env['hr.holiday.planning'].search([('employee_id', '=', id_employee),
                                                                  ('create_date', '>=', first_date)])
            if planning_rc:
                for planning in planning_rc:
                    num_day += planning.number_of_days
        return num_day

    def cron_send_email_real_planning_alert(self):
        today = fields.Date.today()
        real_plannings = self.env['hr.holiday.planning'].search([('state', '=', 'done'), ('date_from', '>', today)])
        if real_plannings:
            for line in real_plannings:
                first_alert = line.company_id.first_alert_real_planning
                second_alert = line.company_id.second_alert_real_planning
                line.date_first_alert = str(fields.Date.from_string(line.date_from) +
                                            relativedelta.relativedelta(days=- first_alert))
                line.date_second_alert = str(fields.Date.from_string(line.date_from) +
                                             relativedelta.relativedelta(days=- second_alert))
                # if line.date_first_alert == today or line.date_second_alert == today:
                #     line.send_notification('email_template_alert_real_planning')
        else:
            pass
