# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        [data] = self.read()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': from_date.strftime('%B %Y'),
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

        employees = self.with_context(active_test=False).employee_ids
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        Payslip = self.env['hr.payslip']

        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            contracts = employee._get_contracts(
                payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
            ).filtered(lambda c: c.active)
            contracts._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
            work_entries = self.env['hr.work.entry'].search([
                ('date_start', '<=', payslip_run.date_end),
                ('date_stop', '>=', payslip_run.date_start),
                ('employee_id', 'in', employees.ids),
            ])
            self._check_undefined_slots(work_entries, payslip_run)

            if(self.structure_id.type_id.default_struct_id == self.structure_id):
                work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
                if work_entries._check_if_error():
                    work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])

                    for work_entry in work_entries.filtered(lambda w: w.state == 'conflict'):
                        work_entries_by_contract[work_entry.contract_id] |= work_entry

                    for contract, work_entries in work_entries_by_contract.items():
                        conflicts = work_entries._to_intervals()
                        time_intervals_str = "\n - ".join(['', *["%s -> %s" % (s[0], s[1]) for s in conflicts._items]])
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Some work entries could not be validated.'),
                            'message': _('Time intervals to look for:%s', time_intervals_str),
                            'sticky': False,
                        }
                    }
            default_values = Payslip.default_get(Payslip.fields_get())
            payslip_values = [dict(default_values, **{
                'name': 'Payslip - %s' % (contract.employee_id.name),
                'employee_id': contract.employee_id.id,
                'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            }) for contract in contracts]

            payslips = Payslip.with_context(tracking_disable=True).create(payslip_values)
            for payslip in payslips:
                payslip._onchange_employee()

            payslips.compute_sheet()
            payslips.calculate_leave_allowances()
            payslip_run.state = 'verify'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
