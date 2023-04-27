# -*- coding:utf-8 -*-

from odoo import fields, models, api, _, tools
from odoo.exceptions import Warning, ValidationError, UserError
from collections import namedtuple
from calendar import monthrange
from datetime import datetime
import logging

from odoo.tools import float_compare, babel
from odoo.tools.float_utils import float_round

from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class hr_holidays(models.Model):
    _inherit = 'hr.leave'

    number_of_days = fields.Float(
        'Duration (Days)', compute='_compute_number_of_days', store=True, readonly=False, copy=False, tracking=True,
        help='Number of days of the time off request. Used in the calculation. To manually correct the duration, use this field.')

    code = fields.Char('Code', size=4, required=False, related='holiday_status_id.code', store=True)
    number_due = fields.Integer("Nombre max dus", related="holiday_status_id.nbre_jr_max")
    date_payment = fields.Date("Date de prise en compte dans la paie")
    subtract_worked_days = fields.Boolean("À déduire des jours travaillés")
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('service', 'Chef de service/ CA'),
        ('department', 'Chef de departement'),
        ('direction', 'Directeur'),
        ('service_admin', 'Service administratif'),
        ('validate', 'Validé'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, tracking=True, copy=False, default='draft', store=True,
        help="The status is set to 'To Submit', when a leave request is created." +
             "\nThe status is 'To Approve', when leave request is confirmed by user." +
             "\nThe status is 'Refused', when leave request is refused by manager." +
             "\nThe status is 'Approved', when leave request is approved by manager.")

    direction_id = fields.Many2one('hr.department', 'Direction', required=False, related="employee_id.direction_id")
    service_id = fields.Many2one('hr.department', 'Service', Required=True, related="employee_id.service_id")
    motif_refus = fields.Text("Motif de refus", required=False)
    company_id = fields.Many2one('res.company', "Société", default=lambda self: self.env.user.company_id.id)
    date_noty_start = fields.Date("Date de notification de depart", compute="_compute_notif_holidays", store=True)
    date_noty_return = fields.Date("Date de notification de retour", compute="_compute_notif_holidays", store=True)
    justification = fields.Binary('Justification', attachment=True)
    vacation_destination = fields.Selection([('out', 'Hors du pays'), ('in', "À l'intérieur du pays")],
                                            'Destination pendant le congé',
                                            default=False, states={'validate': [('readonly', True)]})
    interim_id = fields.Many2one('hr.employee', 'Intérimaire', required=False,
                                 states={'validate': [('readonly', True)]})
    code = fields.Char("Code", related="holiday_status_id.code")
    other_contact = fields.Char("N°Tel/e-mail pendant le congé", required=False,
                                states={'validate': [('readonly', True)]})

    link = fields.Char("Lien", compute="_get_link")
    payslip_id = fields.Many2one('hr.payslip', string='Fiche de paie')
    refuse = fields.Char('Refusé', default='non')
    reprise = fields.Boolean('Reprise de service', default=False)
    date_resumption_service = fields.Datetime('Date de reprise de service')
    payslip_status = fields.Boolean(track_visibility='onchange')
    to_pay = fields.Boolean('A payer', track_visibility='onchange',
                            help="Cliquez sur le bouton si le congé doit être pris en compte dans la prochaine paye")

    @api.depends('payslip_status')
    def reinitialize_leave_allocation(self):
        _logger.info("retwwwweeeeeeeeeeeeeeeeeett")
        self.employee_id.allocation_display = 0

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days(self):
        for holiday in self:
            if holiday.date_from and holiday.date_to:
                if (holiday.date_to - holiday.date_from).days < 30:
                    holiday.number_of_days = \
                        holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['days']
                else:
                    raise Warning("L'employé n'a droit qu'à 30 jours de congés au plus!")
            else:
                holiday.number_of_days = 0

    def send_notification(self, email_id, context=None):
        template_id = self.env['ir.model.data'].get_object_reference('hr_holiday_custom', email_id)
        try:
            mail_templ = self.env['mail.template'].browse(template_id[1])
            result = mail_templ.send_mail(res_id=self.id, force_send=True)
            return True
        except:
            return False

    @api.depends('holiday_status_id')
    def _compute_state(self):
        super(hr_holidays, self)._compute_state()
        for holiday in self:
            if self.env.context.get('unlink') and holiday.state == 'draft':
                # Otherwise the record in draft with validation_type in (hr, manager, both) will be set to confirm
                # and a simple internal user will not be able to delete his own draft record
                holiday.state = 'draft'
            else:
                holiday.state = 'draft' if holiday.validation_type != 'no_validation' else 'draft'

    @api.depends('employee_id')
    def action_submit(self):
        # Fix blocking of requests when a hierarchical level does not exist.
        self.refuse = 'non'
        if self.holiday_status_id.no_validation:
            self.state = 'service_admin'
        else:
            if self.employee_id.type_employee == 'employee':
                if self.service_id:
                    self.state = 'service'
                    # self.send_notification('email_service_template_holidays')
                elif not self.service_id and self.department_id:
                    self.state = 'department'
                    # self.send_notification('email_departement_template_holidays')
                elif not self.service_id and not self.department_id and self.direction_id:
                    self.state = 'direction'
                    # self.send_notification('email_director_template_holidays')
                else:
                    self.state = 'service_admin'
                    # self.send_notification('email_service_admin_template_holidays')

            elif self.employee_id.type_employee == 'service_chief':
                if self.department_id:
                    self.state = 'department'
                    # self.send_notification('email_departement_template_holidays')
                elif not self.department_id and self.direction_id:
                    self.state = 'direction'
                    # self.send_notification('email_director_template_holidays')
                else:
                    self.state = 'service_admin'
                    # self.send_notification('email_service_admin_template_holidays')

            elif self.employee_id.type_employee == 'department_chief':
                if self.direction_id:
                    self.state = 'direction'
                    # self.send_notification('email_director_template_holidays')
                else:
                    self.state = 'service_admin'
                    # self.send_notification('email_service_admin_template_holidays')

            elif self.employee_id.type_employee == 'director':
                self.state = 'service_admin'
                # self.send_notification('email_service_admin_template_holidays')
            else:
                raise UserError(_('The agent is not assigned to a service, a department, or a direction. The request '
                                  'will not be validated.'))
        return True

    def action_chief_service(self):
        # Fix blocking of requests when a hierarchical level does not exist.
        if self.department_id:
            self.state = 'department'
            self.send_notification('email_departement_template_holidays')
        elif not self.department_id and self.direction_id:
            self.state = 'direction'
            # self.send_notification('email_director_template_holidays')
        else:
            self.state = 'service_admin'
            # self.send_notification('email_service_admin_template_holidays')

    def action_chief_department(self):
        # Fix blocking of requests when a hierarchical level does not exist.
        if self.direction_id:
            self.state = 'direction'
            # self.send_notification('email_director_template_holidays')
        else:
            self.state = 'service_admin'
            # self.send_notification('email_service_admin_template_holidays')

    def action_chief_direction(self):
        # Fix blocking of requests when a hierarchical level does not exist.
        self.state = 'service_admin'
        # self.send_notification('email_service_admin_template_holidays')

    @api.depends('company_id')
    def _compute_notif_holidays(self):
        if self.company_id:
            if self.date_from:
                date_start = str(fields.Date.from_string(self.date_from) + relativedelta(
                    days=- self.company_id.days_before_holidays))
                date_to = str(fields.Date.from_string(self.date_to) + relativedelta(
                    days=- self.company_id.days_after_holidays))
                self.date_noty_start = date_start
                self.date_noty_return = date_to

    def action_confirm(self):
        self.write({'state': 'validate'})
        self.activity_update()
        # for hol in self:
        #     hol.send_notification('email_validation_template_holidays')
        return True

    def _get_link(self):
        param_obj = self.env['ir.config_parameter']
        db = self._cr.dbname
        board_link = param_obj.get_param('web.base.url')
        board_link += "/?db=%s#id=%s&view_type=form&model=hr.leave" % (db, self._ids[0])
        return board_link

    def action_validate(self):
        self.state = 'validate'
        self.date_resumption_service = self.employee_id.get_holiday_of_year(self.date_to +
                                                                            relativedelta(days=+1))
        # super().action_validate()
        return self.deduct_annual_leave()

    def action_cancel(self):
        self.write({'state': 'cancel'})
        # self.send_notification('email_cancellation_leave_template')

    def deduct_annual_leave(self):
        """
        Fonction permettant de deduire les conges anticipes des conges annuels
        :return:
        """
        if self.state in ('direction', 'validate') and self.holiday_status_id.code == 'C_AN':
            employe_rc = self.env['hr.employee'].search([('id', '=', self.employee_id.id)])
            employe_rc._get_estimed_holidays()

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        for holiday in self:
            val_type = holiday.holiday_status_id.leave_validation_type
            if state == 'confirm':
                continue

            if state == 'draft':
                continue

            if not is_officer:
                continue

            if is_officer:
                # use ir.rule based first access check: department, members, ... (see security.xml)
                holiday.check_access_rule('write')

            if holiday.employee_id == current_employee and not is_manager:
                continue
                # raise UserError(_('Only a Leave Manager can approve its own requests.'))

            if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager'):
                manager = holiday.employee_id.parent_id or holiday.employee_id.department_id.manager_id
                if (manager and manager != current_employee) and not self.env.user.has_group(
                        'hr_holidays.group_hr_holidays_manager'):
                    raise UserError(_('You must be either %s\'s manager or Leave manager to approve this leave') % (
                        holiday.employee_id.name))

            if state == 'validate' and val_type == 'both':
                if not self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                    if not self.env.user.has_group('hr_holidays.group_hr_holidays_responsible'):
                        raise UserError(_('Only an Leave Manager can apply the second approval on leave requests.'))

    def cron_late_return_leave_alert(self):
        """
        Fonction permettant d'envoyer des notifications aux responsables de la société concernant les retards de
        retour des congés des agents
        :return:
        """

        today = datetime.today()
        alert_date = today - relativedelta(days=1)
        holidays = self.search([('state', '=', 'validate'),
                                ('request_date_to', '=', str(alert_date)[:10])])
        for holiday in holidays:
            holiday_recovery = self.env['hr.holidays.recovery'].search([('holidays_id', '=', holiday.id)])

            if not holiday_recovery:
                email_template_id = self.env.ref('hr_holiday_custom.template_alert_late_return_leave').id
                email_template = self.env['mail.template'].browse(email_template_id)
                email_template.send_mail(holiday.id, force_send=True)

    def createHolidays(self, employee_id, number_of_days):
        type = self.env['hr.holidays.status'].search([('code', '=', 'CONG')], limit=1)
        if type:
            vals = {
                'holidays_type': 'employee',
                'employee_id': employee_id,
                'holidays_status_id': type.id,
                'number_of_days_temps': number_of_days,
            }
            self.create(vals)

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):
        number_of_days = 0
        for record in self:
            if record.date_from and record.date_to:
                if record.holiday_status_id.is_calendar:
                    date_from = fields.Datetime.from_string(record.date_from)
                    date_end = fields.Datetime.from_string(record.date_to)
                    tmp = date_end - date_from
                    number_of_days = tmp.days + 1
                else:
                    number_of_days = record._get_number_of_days(record.date_from, record.date_to, record.employee_id.id)
            record.number_of_days = number_of_days

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        if self.holiday_status_id:
            self.request_date_from = False
            self.request_date_to = False

    # @api.model
    # def computeHoldaysByType(self, date_from, date_to, contract):
    #     res = []
    #     Range = namedtuple('Range', ['start', 'end'])
    #     hstatus = self.env['hr.leave.type'].search([])
    #     r1 = Range(start=date_from, end=date_to)
    #     self._cr.execute("SELECT id FROM hr_leave WHERE ((date_from"
    #                      " between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) OR (date_to"
    #                      " between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')))"
    #                      " AND state='validate' AND type='remove'",
    #                      (str(date_from), str(date_to), str(date_from), str(date_to)))
    #     holidays_ids = [x[0] for x in self._cr.fetchall()]
    #     if holidays_ids:
    #         holidays = self.browse(holidays_ids)
    #         for status in hstatus:
    #             days = 0
    #             temp = holidays.filtered(lambda r: r.holiday_status_id == status)
    #             for tp in temp:
    #                 old_date_from = datetime.strptime(tp.date_from[:10], '%Y-%m-%d')
    #                 old_date_to = datetime.strptime(tp.date_to[:10], '%Y-%m-%d')
    #                 r2 = Range(start=old_date_from, end=old_date_to)
    #                 result = (min(r1.end, r2.end) - max(r1.start, r2.start)).days + 1
    #                 if result > 0:
    #                     days += result
    #             if days != 0:
    #                 vals = {
    #                     'name': status.name,
    #                     'sequence': 5,
    #                     'code': status.code,
    #                     'number_of_days': days,
    #                     'number_of_hours': days * 8,
    #                     'contract_id': contract.id,
    #
    #                 }
    #                 res += [vals]
    #     return res

    @api.model
    def computeHoldaysByType(self, date_from, date_to, contract, employee_id):
        res = []
        Range = namedtuple('Range', ['start', 'end'])
        hstatus = self.env["hr.holidays.status"].search([])
        r1 = Range(start=date_from, end=date_to)
        self._cr.execute("SELECT id FROM hr_holidays WHERE ((date_from"
                         " between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) OR (date_to"
                         " between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')))"
                         " AND state='validate' AND payslip_status = TRUE  AND type='remove' AND employee_id='%s'",
                         (str(date_from), str(date_to),
                          str(date_from), str(date_to), employee_id))
        holidays_ids = [x[0] for x in self._cr.fetchall()]
        if holidays_ids:
            holidays = self.browse(holidays_ids)
            for status in hstatus:
                days = 0
                temp = holidays.filtered(lambda r: r.holiday_status_id == status)
                for tp in temp:
                    old_date_from = datetime.strptime(tp.date_from[:10], '%Y-%m-%d')
                    old_date_to = datetime.strptime(tp.date_to[:10], '%Y-%m-%d')
                    r2 = Range(start=old_date_from, end=old_date_to)
                    result = (min(r1.end, r2.end) - max(r1.start, r2.start)).days + 1
                    if result > 0:
                        days += result
                if days != 0:
                    nb_days = monthrange(date_from.year, date_from.month)
                    if days == nb_days[1]:
                        days = 30
                    hours = days * 173.33 / 30
                    vals = {
                        'name': status.name,
                        'sequence': 5,
                        'code': status.code,
                        'number_of_days': days,
                        'number_of_hours': hours,
                        'contract_id': contract.id,
                    }
                res += [vals]
        return res

    def getHolidays(self, date_from, date_to, employee_id):
        res = []
        self._cr.execute(
            "SELECT sum(number_of_days), holiday_status_id, subtract_worked_days FROM hr_leave WHERE (date_payment"
            " between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))"
            " AND state='validate' AND payslip_status = True AND employee_id = %s AND subtract_worked_days = True "
            "GROUP BY holiday_status_id, subtract_worked_days",
            (str(date_from), str(date_to), employee_id))
        holidays = self._cr.dictfetchall()
        if holidays:
            for holiday in holidays:
                type_holiday = self.env['hr.leave.type'].browse(holiday['holiday_status_id'])
                if type_holiday:
                    val = {
                        'name': type_holiday.name,
                        'code': type_holiday.code,
                        'number_of_days': holiday['sum'],
                        'number_of_hours': holiday['sum'] * 8,
                    }
                    res.append(val)
        return res

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def check_holidays(self):
        for holiday in self:
            if holiday.holiday_type != 'employee' or not holiday.employee_id or \
                    holiday.holiday_status_id.allocation_type == 'no':
                continue
            if holiday.holiday_status_id.allocation_type == 'legal':
                if 0 < holiday.number_due < holiday.number_of_days:
                    raise Warning(("La réglementation vous autorise à prendre au maximum %s jour(s). Merci de faire"
                                   " les corrections nécessaires.") % holiday.number_due)
                else:
                    continue
            else:
                if holiday.holiday_status_id.code == 'CONG':
                    if holiday.employee_id.number_days_estimed_holidays < holiday.number_of_days_display > holiday.employee_id.remaining_leaves:
                        raise ValidationError(
                            _("The number of days you are requesting is more than your forecast. You can take a "
                              "maximum of '%s' days") % (
                                holiday.employee_id.number_days_estimed_holidays))
                # if holiday.holiday_status_id.time_type == 'leave':
                #     if holiday.number_of_days_display > holiday.employee_id.remaining_leaves:
                #         raise ValidationError(
                #             _("The number of days you are requesting is greater than your available days. You can "
                #               "take a maximum of '%s' days") % (
                #                 holiday.employee_id.remaining_leaves))
                #     else:
                #         continue

            leave_days = holiday.holiday_status_id.get_days(holiday.employee_id.id)[holiday.holiday_status_id.id]
            if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or \
                    float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                        'Please also check the leaves waiting for validation.'))


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.leave.type'

    code = fields.Char('Code', size=4, required=False, default='CONG')
    nbre_jr_max = fields.Integer('Nombre de Jours(Max)')
    is_calendar = fields.Boolean('Basé sur les jours calendaires', default=True)
    allocation_type = fields.Selection(selection_add=[('legal', "Fixé par la réglementation en vigueur")])
    no_validation = fields.Boolean('Pas de validation', help="Coché si le congé ne devra pas être validé par l'un des "
                                                             "responsables hiérachiques.Il passera de l'état "
                                                             "'Brouillion' à celui de 'Service Administratif'")

    def name_get(self):
        if not self._context.get('employee_id'):
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            return super(HrHolidaysStatus, self).name_get()
        res = []
        for record in self:
            name = record.name
            if record.allocation_type not in ('no', 'legal'):
                if record.code == 'CONG':
                    employee_rc = self.env['hr.employee'].search([('id', '=', self._context.get('employee_id'))])
                    # Recuperer les conges anticipes de la periode et deduire du total des previsions
                    nbr_days = employee_rc.number_days_estimed_holidays
                    anticipated_leaves = self.env['hr.leave'].search([('employee_id', '=', employee_rc.id),
                                                                      ('request_date_from', '>',
                                                                       employee_rc.date_return_last_holidays),
                                                                      ('holiday_status_id.code', '=', 'C_AN'),
                                                                      ('state', 'in', ('validate', 'service_admin',
                                                                                       'direction'))])
                    if anticipated_leaves:
                        for anticipated_leave in anticipated_leaves:
                            if anticipated_leave.number_of_days_display > 0:
                                nbr_days -= anticipated_leave.number_of_days_display

                    name = "%(name)s (%(count)s)" % {
                        'name': name,
                        'count': _('Forecast: %g / Achieved: %g ') % (
                            float_round(nbr_days, precision_digits=2) or 0.0,
                            float_round(record.max_leaves, precision_digits=2) or 0.0,
                        ) + (_(' hours') if record.request_unit == 'hour' else _(' days'))
                    }
                else:
                    name = "%(name)s (%(count)s)" % {
                        'name': name,
                        'count': _('%g remaining out of %g') % (
                            float_round(record.virtual_remaining_leaves, precision_digits=2) or 0.0,
                            float_round(record.max_leaves, precision_digits=2) or 0.0,
                        ) + (_(' hours') if record.request_unit == 'hour' else _(' days'))
                    }

            res.append((record.id, name))
        return res


class ReportHolidayDecision(models.AbstractModel):
    _name = 'report.hr_holiday_custom.report_hr_holidays'
    _description = 'Holiday Decision Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.leave'].browse(docids)
        if docs.state == 'validate':
            if docs.holiday_status_id.code == 'CMAT':
                if docs.employee_id.gender != 'female':
                    raise Warning("L'employé est un homme! Il ne peut prendre de congé maternité.")
                else:
                    raise Warning("Vous ne pouvez pas imprimer une décision de congé. Imprimé plutôt"
                                  " une décision de congé de maternité")

            else:
                locale = self.env.context.get('lang') or 'en_US'
                request_date_from = tools.ustr(
                    babel.dates.format_date(date=docs.request_date_from, format='dd MMMM y', locale=locale))
                date_resumption_service = tools.ustr(
                    babel.dates.format_date(date=docs.date_resumption_service, format='dd MMMM y', locale=locale))
                return {
                    'doc_ids': docs.ids,
                    'doc_model': 'hr.leave',
                    'docs': docs,
                    'request_date_from': request_date_from,
                    'date_resumption_service': date_resumption_service
                }
        else:
            raise Warning("Vous ne pouvez imprimer de décision de congé , que si elle est validée")


class HrcnceReportHolidayMaternity(models.AbstractModel):
    _name = 'report.hr_holiday_custom.report_hr_holidays_maternity'
    _description = 'Holiday maternity Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.leave'].browse(docids)
        if docs.state == 'validate':
            if docs.employee_id.gender == 'female' and docs.holiday_status_id.code == 'CMAT':
                locale = self.env.context.get('lang') or 'en_US'
                request_date_from = tools.ustr(
                    babel.dates.format_date(date=docs.request_date_from, format='dd MMMM y', locale=locale))
                request_date_to = tools.ustr(
                    babel.dates.format_date(date=docs.request_date_to, format='dd MMMM y', locale=locale))
                return {
                    'doc_ids': docs.ids,
                    'doc_model': 'hr.leave',
                    'docs': docs,
                    'request_date_from': request_date_from,
                    'request_date_to': request_date_to
                }
            else:
                raise Warning("L'employé est un homme ou vous ne pouvez pas imprimer une décision de congé de "
                              "maternité. Imprimer plutôt une décision de congé")
        else:
            raise Warning("Vous ne pouvez imprimer de décision de congé de maternité, que si elle est validée")


class LeaveReport(models.Model):
    _inherit = "hr.leave.report"