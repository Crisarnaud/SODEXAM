# -*- coding:utf-8 -*-

import logging
from odoo import models, api, fields, exceptions, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, ValidationError
from collections import namedtuple
from datetime import datetime

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def checkOverlappingDate(self, slip_date_start, slip_date_to):
        number_of_days = 0
        return number_of_days

    def getWorkedDays(self, date_from, date_to, contract):
        att_obj = self.env['hr.attendance']
        res = []
        hours = 0
        if self.type in ('j', 'h'):
            query_select = """
            SELECT id, check_in, check_out FROM hr_attendance WHERE (check_in
                                 between %(date_from)s
                                 AND
                                 %(date_to)s )
                                 AND
                                (check_out between %(date_from)s
                                 AND
                                  %(date_to)s)
                                 AND
                                  employee_id=%(id)s

            """
            param_query = {
                'date_from': date_from,
                'date_to': date_to,
                'id': self.id
            }
            self.env.cr.execute(query_select, param_query)
            for x in self.env.cr.dictfetchall():
                date_start = fields.Datetime.from_string(x['check_in'])
                date_end = fields.Datetime.from_string(x['check_out'])
                tmp = relativedelta(date_end, date_start)
                hours += tmp.hours
            days = hours / 8
            entry = self.env['hr.work.entry.type'].search([('code', '=', 'WORK100')])
            salary_rule = self.env['hr.salary.rule'].search([('code', '=', 'WORK100')], limit=1)
            vals = {
                'name': _("Nombre de jours travaillés"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': days,
                'number_of_hours': hours,
                'contract_id': contract.id,
                'work_entry_type_id': entry.id,
                'salary_rule_id': salary_rule.id
            }
            res.append(vals)
        else:
            entry = self.env['hr.work.entry.type'].search([('code', '=', 'WORK100')])
            salary_rule = self.env['hr.salary.rule'].search([('code', '=', 'WORK100')], limit=1)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': 30,
                'number_of_hours': 173.33,
                'contract_id': contract.id,
                'work_entry_type_id': entry.id,
                'salary_rule_id': salary_rule.id
            }

            number = self.checkOverlappingDate(date_from, date_to)
            if number:
                attendances['number_of_days'] = attendances['number_of_days'] - number
                attendances['number_of_hours'] = 173.33 * attendances['number_of_days'] / 30
            res.append(attendances)
            return res

    indice = fields.Integer('Indice', store=True)
    annual_leave_payment_date = fields.Date('Date de payement congé')
    leave_balance = fields.Float('Solde congé antérieur')
    leaves_count = fields.Float('Total congés')
    date_return_last_holidays = fields.Date(string="Date de retour Congés")
    date_depart_holidays = fields.Date(string='Date de depart en congés')
    holidays_legal_leaves = fields.Float(string='Congés légaux restants')
    type = fields.Selection(selection_add=[('p', 'Fonctionnaire')])
    is_crrae_contributor = fields.Boolean("Cotise pour la CRRAE", default=False)
    overtime_ids = fields.One2many('hr.attendance.heure.supp', 'employee_id', "Heures supplémentaires")
    date_anciennete = fields.Date("Date d'ancienneté", required=False)
    dispatch_bank_ids = fields.One2many('hr.employee.salary.dispatched.line', 'employee_id', 'Repartition du salaire')

    def getWorkInput(self, contract, date_from, date_to):
        res = []
        overtimes = self.getOvertime(contract.id, date_from, date_to)
        if overtimes:
            res += overtimes
        return res

    def getOvertime(self, contract_id, date_start, date_end):
        res = []
        hstypes = self.env["hr.attendance.heure.supp.type"].search([])
        if hstypes:
            rule = self.env['hr.work.entry.type'].search([('code', '=', 'OUT')])
            for type in hstypes:
                salary_rule = self.env['hr.salary.rule'].search([('code', '=', type.code)], limit=1)
                for sal in salary_rule:
                    total = 0
                    dic = {
                        'code': type.code,
                        'number_of_hours': total,
                        'name': type.name,
                        'contract_id': contract_id,
                        'work_entry_type_id': rule.id,
                        'salary_rule_id': sal.id
                    }
                    overtimes = self.env['hr.attendance.heure.supp'].search([]).filtered(
                        lambda over: date_start <= over.h_date <= date_end and over.state == 'confirmed' and
                                     over.heure_supp_type_id == type and over.employee_id.id == self.id)
                    if overtimes:
                        total = sum([over.nb_heure for over in overtimes])
                        dic['number_of_hours'] = total
                    res.append(dic)
        return res

    @api.onchange('is_crrae_contributor')
    def check_crrae_contributor(self):
        if self.is_crrae_contributor:
            difference = self.age + 10
            if difference > self.company_id.retirement_age:
                raise ValidationError(_("Cet employé est à moins de 10 ans de la retraite, de ce fait il ne peut "
                                        "souscrire à la CRRAE qu'à certaines conditions. Merci de vous rapprocher des "
                                        "gestionnaires de la CRRAE."))

    def getTotalRubriqueByPeriod(self, code, date_from, date_to):
        amount = 0
        payslips = self.slip_ids.filtered(lambda slip: slip.date_from >= date_from and slip.date_to <= date_to)
        if payslips:
            p_lines = self.env['hr.payslip.line'].search([('code', '=', code), ('slip_id', 'in', payslips.ids)])
            if p_lines:
                amount = sum([line.total for line in p_lines])
        return amount

    def getAmountRubriqueByPeriod(self, code, date_from, date_to):
        amount = 0
        payslips = self.slip_ids.filtered(lambda slip: slip.date_from >= date_from and slip.date_to <= date_to)
        if payslips:
            p_lines = self.env['hr.payslip.line'].search([('code', '=', code), ('slip_id', 'in', payslips.ids)])
            if p_lines:
                amount = sum([line.amount for line in p_lines])
        return amount

    def getBaseATPF(self, code, date_from, date_to):
        """
        This function determines the basis for calculating the work accident and family benefit for each month and
        cumulates over the year.
        :param code:
        :param date_from:
        :param date_to:
        :return:
        """
        amount = 0
        max_assiette_autre_contribution = self.company_id.max_assiette_autre_contribution
        payslips = self.slip_ids.filtered(lambda slip: slip.date_from >= date_from and slip.date_to <= date_to)
        if payslips:
            p_lines = self.env['hr.payslip.line'].search([('code', '=', code), ('slip_id', 'in', payslips.ids)])
            if p_lines:
                amount = sum([min(line.amount, max_assiette_autre_contribution) for line in p_lines])
        return amount


class HrEmployeeMotifCloture(models.Model):
    _inherit = 'hr.employee.motif.cloture'

    indemnity = fields.Boolean('Indemnité à calculer', default=False,
                               help="Utilisé pour la détermination des indemnités lors du calcul du solde de "
                                    "tout compte")
