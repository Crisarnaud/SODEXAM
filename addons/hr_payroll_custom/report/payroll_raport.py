# -*- coding: utf-8 -*-

import logging
from datetime import datetime
import time
from odoo import api, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import format_amount

from itertools import groupby

_logger = logging.getLogger(__name__)


class ReportHrPayroll(models.AbstractModel):
    _name = 'report.hr_payroll_custom.report_payroll'
    _description = "Rapport hr_payroll_custom.report_payroll"

    def _lines(self, date_from, date_to, company_id, type_employe):
        _codes_rules = []
        res = {}
        resultats = []
        _headers = ['NOM ET PRENOMS']
        rules = self.env['hr.salary.rule'].search([('appears_on_payroll', '=', True)])
        date_from = date_from
        date_to = date_to
        for rule in rules:
            _headers.append(rule.name)
        _codes_rules = rules.mapped(lambda r: r.code)
        res['codes'] = _codes_rules
        res['headers'] = _headers
        self.env.cr.execute("SELECT id FROM hr_payslip WHERE (date_from between to_date(%s,'yyyy-mm-dd') AND "
                            "to_date(%s,'yyyy-mm-dd')) AND (date_to between to_date(%s,'yyyy-mm-dd') "
                            "AND to_date(%s,'yyyy-mm-dd')) AND company_id = %s",

                            (date_from, date_to, date_from, date_to, company_id))
        payslip_ids = [x[0] for x in self._cr.fetchall()]
        if payslip_ids:
            """Trier les employés par type (mensuel, journalier, horaire) ou tous les employés"""
            if type_employe == 'fonctionnaire':
                payslips_sorted = self.env['hr.payslip'].browse(payslip_ids).sorted(
                    key=lambda r: r.employee_id.identification_id)
                payslips = payslips_sorted.filtered(lambda r: r.employee_id.type == 'm')
            if type_employe == 'mensuel':
                payslips_sorted = self.env['hr.payslip'].browse(payslip_ids).sorted(
                    key=lambda r: r.employee_id.identification_id)
                payslips = payslips_sorted.filtered(lambda r: r.employee_id.type == 'm')
            if type_employe == 'journalier':
                payslips_sorted = self.env['hr.payslip'].browse(payslip_ids).sorted(
                    key=lambda r: r.employee_id.identification_id)
                payslips = payslips_sorted.filtered(lambda r: r.employee_id.type == 'j')
            if type_employe == 'horaire':
                payslips_sorted = self.env['hr.payslip'].browse(payslip_ids).sorted(
                    key=lambda r: r.employee_id.identification_id)
                payslips = payslips_sorted.filtered(lambda r: r.employee_id.type == 'h')
            if type_employe == 'all':
                payslips = self.env['hr.payslip'].browse(payslip_ids).sorted(
                    key=lambda r: r.employee_id.identification_id)
            for employee, lines in groupby(payslips, lambda l: l.employee_id):
                name = employee.name + ' ' + employee.first_name
                vals = {'MATRICULE': employee.identification_id, 'NAME': name, 'type': employee.type}
                slips = list(lines)
                for rule in _codes_rules:
                    amount = 0.0
                    for slip in slips:
                        self.env.cr.execute("SELECT SUM(total) FROM hr_payslip_line WHERE slip_id=%s AND code=%s",
                                            (slip.id, rule))
                        result = self.env.cr.dictfetchall()
                        if result and result[0]['sum'] is None:
                            amount += 0.0
                        else:
                            amount += result[0].get('sum')
                    vals[rule] = amount
                resultats += [vals]
        res['lines'] = resultats
        return res

    def _lines_total(self, codes, lines):
        res = {}
        for code in codes:

            total = 0
            for line in lines:
                if line[code] is not None:
                    total += line[code]
            res[code] = total
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        print('L91 - data', data)