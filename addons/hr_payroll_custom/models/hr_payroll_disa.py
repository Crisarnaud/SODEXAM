from odoo import fields, models, api
import time


class PayrollDisa(models.Model):
    _name = 'hr_disa.payroll_disa'
    _description = 'DISA'

    name = fields.Char('Référence', required=True)
    date_from = fields.Date("Date de début", required=True, default=time.strftime('%Y-01-01'))
    date_to = fields.Date("Date de fin", required=True, default=time.strftime('%Y-12-31'))
    company_id = fields.Many2one('res.company', 'Société', default=1, required=True)
    seq_disa = fields.Char('Sequence', readonly=True)
    total_general_brut = fields.Integer('Total brut annuel', compute='_compute', store=True)
    total_general_retraite = fields.Integer('Total retraite', compute='_compute', store=True)
    total_cotisation_pf_am = fields.Integer(compute='_compute', store=True)
    disa_line_ids = fields.One2many('hr_disa.payroll_disa_line', 'disa_id', 'Ligne disa')
    cumul_contribution_line_ids = fields.One2many('hr_disa.cumul_contribution_line', 'disa_id', 'Cumul des cotisations')
    cnps_monthly_ids = fields.One2many('hr.cnps.monthly', 'disa_id', 'CNPS Mensuel')
    contribution_scheme = fields.Integer('Total cotisation', compute='get_contribution_scheme', store=True)
    total_cnps_monthly = fields.Integer('Total cnps', compute='get_total_cnps_monthly', store=True)

    def computeDisa(self):
        res = []
        employees = self.env['hr.employee'].search([('company_id', '=', self.company_id.id),
                                                    ('type', 'in', ('h', 'j', 'm'))], order='identification_id')

        if employees:
            for emp in employees:
                employee_type = 'M'
                if emp.type == 'j':
                    employee_type = 'J'
                if emp.type == 'h':
                    employee_type = 'H'
                val = {
                    'employee_id': emp.id,
                    'disa_id': self.id,
                    'num_cnps': emp.identification_cnps	 or '',
                    'birthday': emp.birthday.strftime("%d/%m/%Y") if emp.birthday else '',
                    'hiring_date': emp.start_date.strftime("%d/%m/%Y") if emp.start_date else '',
                    'date_of_departure': emp.end_date.strftime("%d/%m/%Y") if emp.end_date else '',
                    'employee_type': employee_type,
                    'work_time': emp.getTotalRubriqueByPeriod('CON', self.date_from, self.date_to) / 30,
                    'total_gross': emp.getTotalRubriqueByPeriod('BRUT', self.date_from, self.date_to),
                    'other_gross': emp.getBaseATPF('BRUT', self.date_from, self.date_to),
                    'cnps_gross': emp.getAmountRubriqueByPeriod('CNPS', self.date_from, self.date_to),
                    'contribution': '1234',
                    'comment': ""
                }
                res.append(val)
        self.disa_line_ids.unlink()
        self.env['hr_disa.payroll_disa_line'].create(res)

        cnps_monthly = self.env['hr.cnps.monthly'].search([('date_from', '>=', self.date_from),
                                                           ('date_to', '<=', self.date_to)])

        cnps_monthly_ids = []
        for cnps_month in cnps_monthly:
            cnps_month.disa_id = self.id
            cnps_monthly_ids.append(cnps_month.id)
        categories = self.env['hr.cnps.monthly.category_line'].search([('cnps_monthly_id', 'in', cnps_monthly_ids)])

        # tranches CNPS
        cnps_slice = self.env['hr.cnps.setting'].search([], order="sequence")
        contribution_scheme = self.env['hr.cnps.cotisation.line.template'].search([], order='sequence')

        if contribution_scheme:
            contribution_scheme_data = []
            for line in contribution_scheme:
                vals = {
                    'name': line.name,
                    'rate': line.taux,
                    'amount_submitted': self.total_general_retraite if line.type == 'cnps' else self.total_cotisation_pf_am,
                    'amount': (line.taux * self.total_general_retraite) / 100 if line.type == 'cnps' else
                    (line.taux * self.total_cotisation_pf_am) / 100,
                    'disa_id': self.id,
                }
                contribution_scheme_data.append(vals)
            self.cumul_contribution_line_ids.unlink()
            self.env['hr_disa.cumul_contribution_line'].create(contribution_scheme_data)

    @api.depends('cumul_contribution_line_ids')
    def get_contribution_scheme(self):
        if self.cumul_contribution_line_ids:
            contribution_scheme = 0
            for line in self.cumul_contribution_line_ids:
                contribution_scheme += line.amount
            self.contribution_scheme = contribution_scheme

    @api.depends('cnps_monthly_ids')
    def get_total_cnps_monthly(self):
        if self.cnps_monthly_ids:
            total_cnps_monthly = 0
            for line in self.cnps_monthly_ids:
                total_cnps_monthly += line.total_cotisation_contributed
            self.total_cnps_monthly = total_cnps_monthly

    @api.depends('disa_line_ids')
    def _compute(self):
        if self.disa_line_ids:
            self.total_general_brut = sum(x.total_gross for x in self.disa_line_ids)
            self.total_cotisation_pf_am = sum(y.other_gross for y in self.disa_line_ids)
            self.total_general_retraite = sum(z.cnps_gross for z in self.disa_line_ids)
        else:
            pass


class PayrollDisaLine(models.Model):
    _name = 'hr_disa.payroll_disa_line'
    _description = "Lignes de la DISA"

    name = fields.Char('Nom et Prénoms', related="employee_id.name")
    identification_id = fields.Char('Matricule', related="employee_id.identification_id", store=True)
    num_cnps = fields.Char('N° C.N.P.S')
    birthday = fields.Char('Date de naissance')
    hiring_date = fields.Char('Date embauche')
    date_of_departure = fields.Char('Date de départ')
    employee_type = fields.Char('Type employé')
    work_time = fields.Integer('Temps de travail')
    total_gross = fields.Integer('Brut total')
    other_gross = fields.Integer('Autre brut')
    cnps_gross = fields.Integer('Brut CNPS')
    natural_advantage = fields.Integer('Avantage en nature')
    contribution = fields.Char('Cotisation')
    comment = fields.Char('Commentaire')
    employee_id = fields.Many2one('hr.employee', 'Employé', required=False)
    disa_id = fields.Many2one('hr_disa.payroll_disa', 'DISA')


class PayrollDisaComplementCumulCategoryLine(models.Model):
    _name = 'hr_disa.cumul_category_line'
    _description = "Cumul des lignes de catégorie"

    name = fields.Char('Désignation')
    amount_submitted = fields.Integer('Salaire soumis à cotisation')
    rate = fields.Integer('Taux')
    amount = fields.Integer('Montant')
    disa_id = fields.Many2one('hr_disa.payroll_disa', 'DISA')


class PayrollDisaComplementCumulContribution(models.Model):
    _name = "hr_disa.cumul_contribution_line"
    _description = "Cumul des cotisations"

    name = fields.Char('Designation')
    amount_submitted = fields.Integer('Salaire soumis à cotisation')
    rate = fields.Float('Taux')
    amount = fields.Integer('Montant')
    disa_id = fields.Many2one('hr_disa.payroll_disa', 'DISA')


class HrCnpsMonthly(models.Model):
    _inherit = "hr.cnps.monthly"

    disa_id = fields.Many2one('hr_disa.payroll_disa', 'DISA')
