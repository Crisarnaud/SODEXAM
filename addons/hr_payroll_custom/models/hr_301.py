# -*- conding:utf-8 -*-

import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class Hr301(models.Model):
    _name = "hr.301"
    _description = "HR 301 Management"

    name = fields.Char("Libellé")
    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    company_id = fields.Many2one('res.company', 'Compagnie', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    account_is = fields.Many2one("account.account", "Compte Comptable associé à IS", required=False)
    account_cn = fields.Many2one("account.account", "Compte Comptable associé à CN", required=False)
    account_igr = fields.Many2one("account.account", "Compte Comptable associé à IGR", required=False)
    versement_ids = fields.One2many("hr.301.versement", "etat_301_id", "Versements ou à Verser", required=False)
    line_ids = fields.One2many("hr.301_line", "etat_301_id", "Lignes", required=False)
    total_employee = fields.Integer("Effectif total", compute="_getSummary", store=True)
    total_employee_local = fields.Integer("Effectif employé Local", compute="_getSummary", store=True)
    total_employee_expat = fields.Integer("Effectif employé Expatrié", compute="_getSummary", store=True)
    total_employee_agricole = fields.Integer("Effectif employé Agricole", compute="_getSummary", store=True)
    total_employee_sal_min = fields.Integer("Effectif total Salaires Min", compute="_getSummary", store=True)
    total_amount_brut_total = fields.Float("Total Brut Total (avant retraitement)", compute="_getSummary", store=True)
    total_natural_advantage_software = fields.Float("Total Avantage en nature logiciel", compute="_getSummary",
                                                    store=True)
    total_natural_advantage_other = fields.Float("Total Avantage en nature autre", compute="_getSummary", store=True)
    total_cash_advantage = fields.Float("Total Avantage en espèce", compute="_getSummary", store=True)
    total_total_gross = fields.Float("Total Brut total (après retraitement)", compute="_getSummary", store=True)
    total_amount_is = fields.Float("Total IS", compute="_getSummary", store=True)
    total_amount_cn = fields.Float("Total CN", compute="_getSummary", store=True)
    total_amount_igr = fields.Float("Total IGR", compute="_getSummary", store=True)
    total_amount_tp = fields.Float("Total Transport", compute="_getSummary", store=True)
    total_amount_af = fields.Float("Total Alloc. Fam.", compute="_getSummary", store=True)
    executive_number = fields.Integer('Cadre', compute="get_headcount_by_category", default=0, store=True)
    agent_control_number = fields.Integer('Maitrise', compute="get_headcount_by_category", default=0, store=True)
    employee_number = fields.Integer('Employés', compute="get_headcount_by_category", default=0, store=True)
    worker_number = fields.Integer('Ouvrier', compute="get_headcount_by_category", default=0, store=True)
    training_tax_ids = fields.One2many('hr.301.training_tax', 'etat_301_id', 'Taxe à la formation')
    total_payroll = fields.Integer("Masse salariale totale", compute="_getSummary", store=True,
                                   help="Masse salariale totale de l'exercice")
    exercise_contribution = fields.Float("Contribution 1,2% sur l'exercice", compute="_getSummary", store=True,
                                         help="Contribution 1,2% sur l'exercice (|16| *1,2%)", default="0.0")
    payments_already_made = fields.Integer("Versements déjà effectués", default="0",
                                           help="Versements déjà effectués au titre de FPC (|15| des 12 mois)")
    commitment_on_plan = fields.Integer("Engagement sur plans (FDFP)", default="0",
                                        help="Engagements sur plans agrée par le FDFP (utilisation directe)")
    payment_to_be_made = fields.Integer("Versement à effectuer", default="0", compute="compute_payment_to_be_made",
                                        store=True,
                                        help="Versement à effectué si |17| est supérieur à |18| + |19| (20 = |17| - ("
                                             "|18| + |19|)")

    def compute(self):
        self._getDefaultData()
        self._getSummary()
        self.get_training_tax()
        return True

    def _getLines(self):
        _query = """
            SELECT 
                e.id  as employee_id,
                e.nature_employe as nature_employee,
                sum(plwds.total) as total_worked_days,			
                sum(plan.total) as natural_advantage_software,
                sum(pli.total) as amount_igr,
                sum(plc.total) as amount_cn,
                sum(plis.total) as amount_is,            
                sum(pltp.total) as amount_tp,
                sum(plaf.total) as amount_af,
                CASE
                    WHEN SUM(plan.total) is NOT NULL THEN (sum(plb.total) - sum(plan.total))
                    ELSE sum(plb.total) 
                END as amount_brut_total
            FROM 
                (SELECT * FROM hr_payslip WHERE date_from >= %(date_from)s AND date_to <= %(date_to)s) p
                left join hr_employee e on (p.employee_id = e.id) 
                left join hr_payslip_line plwds on (plwds.employee_id = e.id and plwds.slip_id = p.id and 
                plwds.code = 'TJRPAY')
                left join hr_payslip_line plb on (plb.employee_id = e.id and plb.slip_id = p.id and plb.code = 'BRUT')
                left join hr_payslip_line pli on (pli.employee_id = e.id and pli.slip_id = p.id and pli.code = 'IGR')
                left join hr_payslip_line plc on (plc.employee_id = e.id and plc.slip_id = p.id and plc.code = 'CN')
                left join hr_payslip_line plis on (plis.employee_id = e.id and plis.slip_id = p.id and 
                plis.code = 'ITS')
                left join hr_payslip_line pltp on (pltp.employee_id = e.id and pltp.slip_id = p.id and 
                pltp.code = 'TRSP')
                left join hr_payslip_line plaf on (plaf.employee_id = e.id and plaf.slip_id = p.id and 
                plaf.code = 'ALL_FAM')
                left join hr_payslip_line plan on (plan.employee_id = e.id and plan.slip_id = p.id and 
                plan.salary_rule_id 
                in (select id from hr_salary_rule where natural_advantage is True))						
            GROUP BY
            e.id,
            e.nature_employe      
            
        """
        _params = {
            "date_from": self.date_from,
            "date_to": self.date_to
        }

        self.env.cr.execute(_query, _params)
        results = self.env.cr.dictfetchall()

        return results

    def computeVersementSummury(self, lines):
        if lines:
            amount_total_out = sum([x['amount_total'] for x in lines if x['amount_total'] and x['type'] == 'out'])
            amount_is_out = sum([x['amount_is'] for x in lines if x['amount_is'] and x['type'] == 'out'])
            amount_igr_out = sum([x['amount_cn'] for x in lines if x['amount_cn'] and x['type'] == 'out'])
            amount_cn_out = sum([x['amount_igr'] for x in lines if x['amount_igr'] and x['type'] == 'out'])
            local_employee_out = sum([x['amount_is'] for x in lines if x['amount_is'] and x['type'] == 'out'])
            expat_employee_out = 0
            val = {
                'month': 0,
                'date': '',
                'amount_total': amount_total_out,
                'type': 'out',
                'amount_is': amount_is_out,
                'amount_cn': amount_cn_out,
                'amount_igr': amount_igr_out,
                'local_employee': local_employee_out,
                'expat_employee': expat_employee_out
            }

            return val

    def _getDefaultData(self):
        self.line_ids.unlink()
        data = []
        if not self.versement_ids:
            for i in range(12):
                val = {
                    'month': i + 1,
                    'date': False,
                    'amount_total': 0,
                    'type': 'out',
                    'amount_is': 0,
                    'amount_cn': 0,
                    'amount_igr': 0,
                    'local_employee': 0,
                    'expat_employee': 0,
                }
                data.append(val)
        else:
            for line_versement in self.versement_ids.filtered(lambda fl: fl.month <= 12):
                val = {
                    'month': line_versement.month,
                    'date': line_versement.date,
                    'amount_total': line_versement.amount_total,
                    'type': line_versement.type,
                    'amount_is': line_versement.amount_is,
                    'amount_cn': line_versement.amount_cn,
                    'amount_igr': line_versement.amount_igr,
                    'local_employee': line_versement.local_employee,
                    'expat_employee': line_versement.expat_employee,
                }
                data.append(val)
            self.versement_ids.unlink()

        lines = self._getLines()

        if lines:
            natural_advantage_software = sum(
                [x['natural_advantage_software'] for x in lines if x['natural_advantage_software']])
            amount_total = sum(
                [x['amount_brut_total'] for x in lines if x['amount_brut_total']]) + natural_advantage_software
            amount_is = sum([x['amount_is'] for x in lines if x['amount_is']])
            amount_igr = sum([x['amount_cn'] for x in lines if x['amount_cn']])
            amount_cn = sum([x['amount_igr'] for x in lines if x['amount_igr']])
            local_employee = sum([x['amount_is'] for x in lines if x['nature_employee'] == 'local' and x['amount_is']])
            expat_employee = sum([x['amount_is'] for x in lines if x['nature_employee'] == 'expat' and x['amount_is']])
            val = {
                'month': 14,
                'date': fields.Date.today(),
                'amount_total': amount_total,
                'type': 'in',
                'amount_is': amount_is,
                'amount_cn': amount_cn,
                'amount_igr': amount_igr,
                'local_employee': local_employee,
                'expat_employee': expat_employee,
            }
            data.append(val)
            self.line_ids = self.line_ids.create(lines)
            cumul_out = self.computeVersementSummury(data)
            if cumul_out:
                val = {
                    'month': 13,
                    'amount_total': amount_total - cumul_out['amount_total'],
                    'type': 'in',
                    'amount_is': amount_is - cumul_out['amount_is'],
                    'amount_cn': amount_cn - cumul_out['amount_cn'],
                    'amount_igr': amount_igr - cumul_out['amount_igr'],
                    'local_employee': local_employee - cumul_out['local_employee'],
                    'expat_employee': expat_employee - cumul_out['expat_employee'],
                }
                data.append(val)
        self.versement_ids = self.versement_ids.create(data)

    def _getSummary(self):
        for rec in self:
            if rec.line_ids:
                total_employee = len(rec.line_ids)
                rec.total_employee = total_employee
                count_local_employee = 0
                count_expat_employee = 0
                total_amount_brut_total = 0
                total_natural_advantage_software = 0
                total_natural_advantage_other = 0
                total_cash_advantage = 0
                total_total_gross = 0
                total_amount_is = 0
                total_amount_cn = 0
                total_amount_igr = 0
                total_amount_tp = 0
                total_amount_af = 0

                for line in rec.line_ids:
                    if line.employee_id.nature_employe == 'local':
                        count_local_employee += 1
                    if line.employee_id.nature_employe == 'expat':
                        count_expat_employee += 1
                    total_amount_brut_total += line.amount_brut_total
                    total_natural_advantage_software += line.natural_advantage_software
                    total_natural_advantage_other += line.natural_advantage_other
                    total_cash_advantage += line.cash_advantage
                    total_total_gross += line.total_gross
                    total_amount_is += line.amount_is
                    total_amount_cn += line.amount_cn
                    total_amount_igr += line.amount_igr
                    total_amount_tp += line.amount_tp
                    total_amount_af += line.amount_af

                self.total_employee_local = count_local_employee
                self.total_employee_expat = count_expat_employee
                self.total_employee_agricole = 0
                self.total_amount_brut_total = total_amount_brut_total
                self.total_natural_advantage_software = total_natural_advantage_software
                self.total_natural_advantage_other = total_natural_advantage_other
                self.total_cash_advantage = total_cash_advantage
                self.total_total_gross = total_total_gross
                self.total_amount_is = total_amount_is
                self.total_amount_cn = total_amount_cn
                self.total_amount_igr = total_amount_igr
                self.total_amount_tp = total_amount_tp
                self.total_amount_af = total_amount_af
                self.total_payroll = total_total_gross
                self.exercise_contribution = int(total_total_gross * 0.012)

    @api.depends('line_ids')
    def get_headcount_by_category(self):
        if self.line_ids:
            executive_number = 0
            agent_control_number = 0
            employee_number = 0
            worker_number = 0
            for rec in self.line_ids:
                if rec.category_employee_code == 'CS' or rec.category_employee_code == 'CA':
                    executive_number += 1
                if rec.category_employee_code == 'AM':
                    agent_control_number += 1
                if rec.category_employee_code == 'EM':
                    employee_number += 1
                if rec.category_employee_code == 'OU':
                    worker_number += 1

            self.executive_number = executive_number
            self.agent_control_number = agent_control_number
            self.employee_number = employee_number
            self.worker_number = worker_number

    def get_training_tax(self):
        res = []
        tax_fdfp = self.env['hr.fdfp.config'].search([])
        if tax_fdfp:
            for line in tax_fdfp:
                vals = {
                    'name': line.rule_id.name,
                    'tax': line.taux,
                    'sequence': line.sequence,
                    'gross_salary': self.total_total_gross,
                    'tax_amount': self.total_total_gross * line.taux / 100,
                    'fdfp_config_id': line.id,
                    'etat_301_id': self.id
                }
                res.append(vals)
        if res:
            self.training_tax_ids.unlink()
            self.env['hr.301.training_tax'].create(res)
            return True
        return False

    @api.depends('total_payroll', 'exercise_contribution', 'payments_already_made', 'commitment_on_plan')
    def compute_payment_to_be_made(self):
        payment_to_be_made = self.exercise_contribution - (self.payments_already_made + self.commitment_on_plan)
        if payment_to_be_made > 0:
            self.payment_to_be_made = payment_to_be_made
        else:
            self.payment_to_be_made = 0


class Hr301Line(models.Model):
    _name = "hr.301_line"
    _description = "Line 301 management"
    _rec_name = "employee_id"

    employee_id = fields.Many2one("hr.employee", "Employé", required=True)
    nature_employee = fields.Selection([('local', 'Local'), ('expat', 'Expat')], string="Nature employé",
                                       required=False)
    category_employee_code = fields.Char('Catégorie', related='employee_id.category_contract_id.code', store=True)
    total_worked_days = fields.Float("Total jours travaillés/Congés")
    amount_brut_total = fields.Float("Brut Total (avant retraitement)")
    natural_advantage_software = fields.Float('Avantage en nature logiciel')
    natural_advantage_other = fields.Float('Avantage en nature autre')
    cash_advantage = fields.Float('Avantage en espèce')
    total_gross = fields.Float('Brut total (après retraitement)', compute='compute_total_gross', store=True)
    amount_is = fields.Float("IS", compute='compute_total_gross', store=True)
    amount_cn = fields.Float("CN", compute='compute_total_gross', store=True)
    amount_igr = fields.Float("IGR", compute='compute_total_gross', store=True)
    amount_tp = fields.Float('Transport')
    amount_af = fields.Float('Alloc. Fam.')
    etat_301_id = fields.Many2one("hr.301", "Etat 301", ondelete='cascade')

    @api.depends('natural_advantage_other', 'cash_advantage')
    def compute_total_gross(self):
        for rec in self:
            total_gross = rec.amount_brut_total + rec.natural_advantage_software + rec.natural_advantage_other + \
                          rec.cash_advantage
            rec.total_gross = total_gross

            # Calculation of net taxable salary (SNI)
            net_taxable_salary = round(rec.total_gross * 0.8)

            # Calculation of payroll tax (IS)
            payroll_tax = round(net_taxable_salary * 0.015)
            self.amount_is = payroll_tax

            # National contribution calculation (CN)
            if net_taxable_salary <= 600000:
                national_contribution = 0
            elif 600000 < net_taxable_salary <= 1465000:
                national_contribution = round((net_taxable_salary * 0.015) - 9000)
            elif 1465000 < net_taxable_salary <= 2400000:
                national_contribution = round((net_taxable_salary * 0.05) - 63600)
            elif 2400000 < net_taxable_salary:
                national_contribution = round((net_taxable_salary * 0.1) - 183600)
            else:
                national_contribution = 0
            rec.amount_cn = national_contribution

            # Calculation of general income tax (IGR)
            net_taxable_income = round(((0.8 * total_gross) - (payroll_tax + national_contribution)) * 0.85)
            number_of_shares = rec.employee_id.part_igr
            family_quotient = round(net_taxable_income / number_of_shares)

            if family_quotient <= 300000:
                general_income_tax = 0
            elif 300000 < family_quotient <= 547000:
                general_income_tax = (net_taxable_income * 10 / 110) - (27273 * number_of_shares)
            elif 547000 < family_quotient <= 979000:
                general_income_tax = (net_taxable_income * 15 / 115) - (48913 * number_of_shares)
            elif 979000 < family_quotient <= 1519000:
                general_income_tax = (net_taxable_income * 20 / 120) - (84375 * number_of_shares)
            elif 1519000 < family_quotient <= 2644000:
                general_income_tax = (net_taxable_income * 25 / 125) - (135000 * number_of_shares)
            elif 2644000 < family_quotient <= 4669000:
                general_income_tax = (net_taxable_income * 35 / 135) - (291667 * number_of_shares)
            elif 4669000 < family_quotient <= 10106000:
                general_income_tax = (net_taxable_income * 45 / 145) - (530172 * number_of_shares)
            elif 10106000 < family_quotient:
                general_income_tax = (net_taxable_income * 60 / 160) - (1183594 * number_of_shares)
            else:
                general_income_tax = 0

            rec.amount_igr = round(general_income_tax)


class HR301Versement(models.Model):
    _name = "hr.301.versement"
    _description = "HR 301 Versement management"
    _order = 'month'

    month = fields.Integer("Mois", required=False)
    date = fields.Date("Date", required=False)
    amount_total = fields.Float("Montant global des montants versés ou à verser")
    type = fields.Selection([('out', 'Versement'), ('in', "À verser")], default=False, required=True)
    amount_is = fields.Float("IS")
    amount_cn = fields.Float("CN")
    amount_igr = fields.Float("IGR")
    local_employee = fields.Float("Employé Local")
    expat_employee = fields.Float("Employé Expatrié")
    etat_301_id = fields.Many2one("hr.301", "Etat 301", ondelete='cascade')


class HR301TrainingTax(models.Model):
    _name = 'hr.301.training_tax'
    _description = "Taxe à la formation"

    name = fields.Char('Taxe')
    sequence = fields.Integer('Sequence')
    tax = fields.Float('Taux')
    gross_salary = fields.Integer('Salaire BRUT')
    tax_amount = fields.Integer('Montant')
    fdfp_config_id = fields.Many2one('hr.fdfp.config', 'Taxe FDFP')
    etat_301_id = fields.Many2one("hr.301", "Etat 301", ondelete='cascade')
