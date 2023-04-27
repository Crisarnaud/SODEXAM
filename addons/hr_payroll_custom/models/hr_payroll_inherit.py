import babel
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class HrPayslipRunSalaryDispatched(models.Model):
    _name = "hr.payslip_run.salary_dispatched"
    _description = "Distribution du salaire par masse"
    _rec_name = "bank_id"

    bank_id = fields.Many2one('res.bank', 'Banque', required=True)
    amount = fields.Integer("Montant à viré", required=True)
    payslip_run_id = fields.Many2one('hr.payslip.run', 'Lot de bulletin')


class HrContracts(models.Model):
    _inherit = 'hr.contract'
    _description = 'hr.contract'

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = self.mapped('structure_type_id')
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'
    _description = 'Contract Type'

    @api.model
    def _get_parent(self):
        return self.env.ref('hr_payroll.structure_base', False)

    parent_id = fields.Many2one('hr.payroll.structure', string='Parent', default=_get_parent)

    def _get_parent_structure(self):
        parent = self.mapped('parent_id')
        if parent:
            parent = parent._get_parent_structure()
        return parent


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'
    _description = 'hr.payroll.structure'

    rule_ids = fields.One2many('hr.salary.rule', 'struct_id', string='Salary Rules')

    def get_all_rules(self):
        """
        @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
        """
        all_rules = []
        for struct in self:
            all_rules += struct.rule_ids._recursive_search_of_rules()
        return all_rules


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'