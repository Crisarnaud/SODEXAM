# -*- coding:utf-8 -*-
from math import ceil
import logging
from dateutil import relativedelta

from odoo import api, models, fields, _
from odoo.exceptions import AccessError
from datetime import datetime, date, timedelta

from odoo.tools import float_round


_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    leaves_count = fields.Float('Number of Time Off', compute='_compute_leaves_count')
    remaining_leaves = fields.Float(
        compute='_compute_remaining_leaves', string='Remaining Legal Leaves',
        help='Total number of legal leaves allocated to this employee, change this value to create allocation/leave request. '
             'Total based on all the leave types without overriding limit.')

    payment_date_last_holiday = fields.Date('Date de paiement dernier congé')
    brut_holiday = fields.Integer("Brut congés en fin d'année")
    current_leave_state = fields.Selection(compute='_compute_leave_status', string="Current Leave Status",
                                           selection_add=[('technical', 'Technical'), ('not_technical', 'No Technical'),
                                                          ('chef_service', 'Chef de service'),
                                                          ('crh', 'Chargé des RH'),
                                                          ('chef_depart', 'Chef de departement'), ('cdaf', 'RAF'), ])
    date_return_last_holidays = fields.Date(string="Date de retour Congés")
    date_depart_holidays = fields.Date(string='Date de depart en congés')
    holidays_legal_leaves = fields.Float(string='Congés légaux restants')
    date_compute_holidays = fields.Date("Date attribution allocation", compute="_get_date_compute_holidays")
    estimed_date_leave = fields.Date("Date prévisonnelle de depart en congés", compute="_get_estimed_holidays",
                                     store=True)
    number_days_estimed_holidays = fields.Integer("Nombre de jours de congés estimés", compute="_get_estimed_holidays",
                                                  store=True)
    estimated_date_return_leave = fields.Date("Date prévisonnelle de retour de congés", compute="_get_estimed_holidays",
                                              store=True)
    stock_holiday = fields.Integer('Stock congé', default=0)
    stock_total_holiday = fields.Integer('Stock total congé', compute='compute_stock_total_holiday', default=0,
                                         store=True)
    planning_save = fields.One2many('save.planning.holiday', 'employee_id', 'Congé')
    save_stock_holiday_ids = fields.One2many('save.stock.holiday', 'employee_id', 'Historique Stock congé')
    holiday_decoration = fields.Float('Nombre de jours supplémentaires (Décoration)', default=0)

    def _compute_leaves_count(self):
        all_leaves = self.env['hr.leave.report'].read_group([
            ('employee_id', 'in', self.ids),
            ('holiday_status_id.allocation_type', '!=', 'no'),
            ('holiday_status_id.active', '=', 'True'),
            ('number_of_days', '>=', 0),
            ('leave_type', '=', 'allocation'),
            ('state', '=', 'validate')
        ], fields=['number_of_days', 'employee_id'], groupby=['employee_id'])
        mapping = dict([(leave['employee_id'][0], leave['number_of_days']) for leave in all_leaves])
        for employee in self:
            employee.leaves_count = float_round(mapping.get(employee.id, 0), precision_digits=2)

    def _compute_remaining_leaves(self):
        remaining = {}
        if self.ids:
            remaining = self._get_remaining_leaves()
        for employee in self:
            value = float_round(remaining.get(employee.id, 0.0), precision_digits=2)
            employee.leaves_count = value
            employee.remaining_leaves = value

    def _get_remaining_leaves(self):
        """ Helper to compute the remaining leaves for the current employees
            :returns dict where the key is the employee id, and the value is the remain leaves
        """
        self._cr.execute("""
            SELECT
                sum(h.number_of_days) AS days,
                h.employee_id
            FROM
                (
                    SELECT holiday_status_id, number_of_days,
                        state, employee_id
                    FROM hr_leave_allocation
                    UNION ALL
                    SELECT holiday_status_id, (number_of_days * -1) as number_of_days,
                        state, employee_id
                    FROM hr_leave
                ) h
                join hr_leave_type s ON (s.id=h.holiday_status_id)
            WHERE
                s.active = true AND h.state='validate' AND
                (s.allocation_type='fixed' OR s.allocation_type='fixed_allocation') AND
                h.employee_id in %s
            GROUP BY h.employee_id""", (tuple(self.ids),))
        return dict((row['employee_id'], row['days']) for row in self._cr.dictfetchall())

    def save_planning_holiday(self):
        """
        Fonction permettant de sauvegarder le planning des congés et de générer automatiquement un nouveau planning
        :return:
        """
        today = fields.Datetime.now()
        employee = self.env['hr.employee'].search([('estimated_date_return_leave', '=', today)])
        if employee:
            for emp in employee:
                val = {
                    'estimed_date_leave': emp.estimed_date_leave,
                    'estimated_date_return_leave': emp.estimated_date_return_leave,
                    'number_days_estimed_holidays': emp.number_days_estimed_holidays,
                    'date_return_last_holidays': emp.date_return_last_holidays,
                    'employee_id': emp.id,
                }
                self.env['save.planning.holiday'].create(val)
                emp.write({'date_return_last_holidays': emp.estimated_date_return_leave})

    def cron_create_stock_holiday(self):
        """
        Fonction permettant de sauvegarder le stock congé au 31 décembre de chaque agent
        :return:
        """
        year = fields.Date.today().year
        employees = self.env['hr.employee'].search([])
        for emp in employees:
            vals = {
                'employee_id': emp.id,
                'name': year,
                'number_days': ceil(emp.remaining_leaves)
            }
            try:
                self.env['save.stock.holiday'].create(vals)
            except:
                continue

    def cron_create_holiday_provision(self):
        """
        Fonction permettant de créer des provisions congés des agents afin de prendre en compte le stock congé à la mise
        en place du projet
        :return:
        """
        employees = self.env['hr.employee'].search([])
        previous_year = fields.Date.today() + relativedelta.relativedelta(years=-1)
        if len(employees) > 0:
            res = []
            res_stock = []
            id_annual_holiday = self.env['hr.leave.type'].search([('code', '=', 'CONG')]).id
            for employee in employees:
                vals = {
                    'name': "Prise en compte du stock congé (année antérieure)",
                    'holiday_status_id': id_annual_holiday if id_annual_holiday else '',
                    'number_of_days': employee.stock_holiday,
                    'number_of_days_display': employee.stock_holiday,
                    'holiday_type': 'employee',
                    'employee_id': employee.id,
                    'state': 'validate'
                }
                res.append(vals)

                vals_stock = {
                    'name': previous_year.year,
                    'employee_id': employee.id,
                    'number_days': employee.stock_holiday
                }
                res_stock.append(vals_stock)

            try:
                self.env['hr.leave.allocation'].create(res)
                self.env['save.stock.holiday'].create(res_stock)
            except:
                pass
        emps = self.env['hr.employee'].search([])
        for emp in emps:
            emp.compute_stock_total_holiday()

    @api.depends('stock_holiday', 'number_days_estimed_holidays')
    def compute_stock_total_holiday(self):
        previous_year = datetime.now() + relativedelta.relativedelta(years=-1)
        for rec in self:
            previous_stock = self.env['save.stock.holiday'].search(
                [('name', '=', previous_year.year), ('employee_id', '=', rec.id)], limit=1)
            rec.stock_total_holiday = previous_stock.number_days if previous_stock else 0
            if rec.estimed_date_leave and rec.estimed_date_leave.year == datetime.now().year:
                rec.stock_total_holiday += rec.number_days_estimed_holidays

    def get_holiday_of_year(self, date):
        """
        Fonction permettant de renvoyer la date du jour ouvrable le plus proche de la date qu'elle a reçu en paramètre
        :param date: date dont on veut vérifier si le jour est ouvrable ou férié (y compris les week-end)
        :return: date du jour ouvrable
        """
        if date.weekday() == 5:
            date = date + relativedelta.relativedelta(days=+2)
        if date.weekday() == 6:
            date = date + relativedelta.relativedelta(days=+1)
        is_holiday = self.env['hr.jour.ferie'].search([('date', '=', date)], limit=1)

        if not is_holiday:
            holidays = self.env['hr.jour.ferie'].search([('is_recurring', '=', True)])
            if holidays:
                for holiday in holidays:
                    is_holiday = all(getattr(holiday.date, x) == getattr(date, x) for x in ['month', 'day'])
                    if is_holiday:
                        break
        while is_holiday:
            date = date + relativedelta.relativedelta(days=+1)
            is_holiday = self.env['hr.jour.ferie'].search([('date', '=', date)], limit=1)
            if not is_holiday:
                holidays = self.env['hr.jour.ferie'].search([('is_recurring', '=', True)])
                if holidays:
                    for holiday in holidays:
                        is_holiday = all(getattr(holiday.date, x) == getattr(date, x) for x in ['month', 'day'])
                        if is_holiday:
                            break
        if date.weekday() == 5:
            date = date + relativedelta.relativedelta(days=+2)
        if date.weekday() == 6:
            date = date + relativedelta.relativedelta(days=+1)
        return date

    @api.depends("date_return_last_holidays", "start_date")
    def _get_estimed_holidays(self):
        """"
        Estimer la période de congé
        """
        today = fields.Datetime.now()
        for emp in self:
            if emp.date_return_last_holidays:
                nbr_days = 0
                facteur = emp.company_id.number_holidays_locaux if emp.nature_employe == 'local' \
                    else emp.company_id.number_holidays_expat
                if emp.date_return_last_holidays:
                    vals = {
                        'estimed_date_leave': False,
                        'number_days_estimed_holidays': 0,
                        'estimated_date_return_leave': False
                    }
                    if emp.date_return_last_holidays == emp.start_date:
                        vals['estimed_date_leave'] = fields.Date.from_string(emp.start_date) + \
                                                     relativedelta.relativedelta(year=today.year, day=+1)
                    else:
                        vals['estimed_date_leave'] = fields.Date.from_string(emp.date_return_last_holidays) + \
                                                     relativedelta.relativedelta(years=+1)

                    # Check if the departure date falls on a Saturday or Sunday
                    if vals['estimed_date_leave'].weekday() == 5:
                        vals['estimed_date_leave'] = vals['estimed_date_leave'] + \
                                                     relativedelta.relativedelta(days=+2)
                    if vals['estimed_date_leave'].weekday() == 6:
                        vals['estimed_date_leave'] = vals['estimed_date_leave'] + \
                                                     relativedelta.relativedelta(days=+1)

                    # check if the departure date of leave is holiday
                    vals['estimed_date_leave'] = self.get_holiday_of_year(vals['estimed_date_leave'])
                    base = facteur * 12 + nbr_days
                    nbr_days = round((base + base / 6)-1)
                    vals['number_days_estimed_holidays'] = nbr_days
                    number_calendar_days = ceil(vals['number_days_estimed_holidays'])
                    vals['estimated_date_return_leave'] = vals['estimed_date_leave'] + relativedelta.relativedelta(
                        days=+number_calendar_days)

                    # Check if the return date of leave falls on a Saturday or a Sunday
                    if vals['estimated_date_return_leave'].weekday() == 5:
                        vals['estimated_date_return_leave'] = vals['estimated_date_return_leave'] + \
                                                              relativedelta.relativedelta(days=+2)
                    if vals['estimated_date_return_leave'].weekday() == 6:
                        vals['estimated_date_return_leave'] = vals['estimated_date_return_leave'] + \
                                                              relativedelta.relativedelta(days=+1)
                    # check if the return date of leave is holiday
                    vals['estimated_date_return_leave'] = self.get_holiday_of_year(vals['estimated_date_return_leave'])

                    emp.update(vals)

    @api.model
    def compute_holidays_auto(self):
        this_date = date.today()
        type = self.env['hr.leave.type'].search([('code', '=', 'CONG')], limit=1)
        if type:
            for emp in self.search([]):
                if emp.start_date:
                    temp_date = fields.Date.from_string(emp.start_date) + relativedelta.relativedelta(
                        month=this_date.month,
                        year=this_date.year)
                    if temp_date == this_date:
                        vals = {
                            'holiday_type': 'employee',
                            'employee_id': emp.id,
                            'holiday_status_id': type.id
                        }
                        if emp.nature_employe == 'local':
                            vals['number_of_days'] = emp.company_id.number_holidays_locaux
                        else:
                            vals['number_of_days'] = emp.company_id.number_holidays_expat
                        holidays = self.env['hr.leave.allocation'].create(vals)
                        if holidays:
                            holidays.action_validate()
        return True

    @api.model
    def compute_holidays_anciennete_auto(self):
        this_date = date.today()
        type = self.env['hr.leave.type'].search([('code', '=', 'CONG')], limit=1)
        if type:
            for emp in self.search([]):
                vals = {
                    'holiday_type': 'employee',
                    'employee_id': emp.id,
                    'holiday_status_id': type.id,
                }
                temp_date = fields.Date.from_string(emp.start_date) + relativedelta.relativedelta(year=this_date.year)
                if emp.start_date and this_date == temp_date:
                    tmp = relativedelta.relativedelta(this_date, temp_date)
                    if 5 <= tmp.years < 10:
                        vals['number_of_days'] = 1
                    elif 10 <= tmp.years < 15:
                        vals['number_of_days'] = 2
                    elif 15 <= tmp.years < 20:
                        vals['number_of_days'] = 3
                    elif 20 <= tmp.years < 25:
                        vals['number_of_days'] = 5
                    elif 25 <= tmp.years < 30:
                        vals['number_of_days'] = 7
                    else:
                        if tmp.years >= 30:
                            vals['number_of_days'] = 8
                holidays = self.env['hr.leave.allocation'].create(vals)
                if holidays:
                    holidays.action_validate()
        return True

    def _get_date_compute_holidays(self):
        this_date = date.today()
        for emp in self:
            date_compute_holidays = fields.Date.from_string(emp.start_date) + relativedelta.relativedelta(
                year=this_date.year)
            emp.date_compute_holidays = date_compute_holidays

    def getInputsPayroll(self, contract, date_from, date_to):
        """ fonction permettant d'inserer la cotisation MUDEXAM FAS et retenue synadexam sur la
        fiche de paie pour le calcul"""
        res = super(HrEmployee, self).getInputsPayroll(contract, date_from, date_to)
        input_mud_fas = self.env['hr.salary.rule'].search([('code', '=', 'RET_MUD_FAS')], limit=1)
        val = {
            'name': "MUDEXAM FAS",
            'code': "RET_MUD_FAS",
            'amount': input_mud_fas.amount_fix,
            'contract_id': contract.id,
            'salary_rule_id': input_mud_fas.id,
        }
        res += [val]

        input_ret_pens_civle = self.env['hr.salary.rule'].search([('code', '=', 'RET_PEN_CIV')], limit=1)
        if self.type == 'p':
            val = {
                'name': "RET. Pension Civile",
                'code': "RET_PEN_CIV",
                'amount': self.indice * 233.457 * 0.0833,
                'contract_id': contract.id,
                'salary_rule_id': input_ret_pens_civle.id,
            }
            res += [val]
        return res


class HrHolidayAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
