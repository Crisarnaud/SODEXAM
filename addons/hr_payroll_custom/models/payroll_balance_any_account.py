# -*- encoding: utf-8 -*-
from math import ceil

from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import datetime
from dateutil import relativedelta
from math import ceil


class PayrollBalanceAnyAccount(models.Model):
    _name = 'hr_payroll_ci.balance_any_account'
    _description = 'Gestion des soldes de tout compte'

    def get_default_end_date(self):
        date = fields.Date.from_string(fields.Date.today())
        return date.strftime('%Y') + '-' + date.strftime('%m') + '-' + date.strftime('%d')

    def _get_employee_id(self):
        return self.env.context.get ('active_id')

    name = fields.Char('Référence', compute='get_employee_info', store=True, readonly=False)
    other_indemnity = fields.Integer('Autre indemnité', default=0, help="Ajouter les autres indemnités: voitures...")
    total_gross = fields.Integer('Total BRUT', help="Somme des BRUTS des 12 derniers salaires et des autres indemnités")
    average_gross = fields.Integer('Moyenne BRUT', help="Moyenne de Total BRUT sur 12 mois")
    sum_salary_elements = fields.Integer('Cumul éléments du salaire', default=0, compute='get_sum_salary_elements',
                                         help="Somme des éléments du salaire")
    hiring_date = fields.Date("Date d'embauche", compute='get_employee_info', store=True)
    end_date = fields.Date('Date de sortie Effective ', default=get_default_end_date,
                           help="Date d'arrêt effectif de service. Elle peut être différente de la date de sortie "
                                "prévisionnelle si l'employé de fais pas son préavis dans les normes.")
    medal_leave = fields.Integer('Jours ouvrables pour médaille', default=0,
                                 help="Nombre de jours ouvrables supplémentaires dû à l'obtention d'une médaille ")
    seniority = fields.Integer('Ancienneté', default=0, compute='get_seniority', store=True, help="Estimée en jour")
    seniority_days = fields.Integer('Jours', compute='get_seniority', store=True)
    seniority_months = fields.Integer('Mois', compute='get_seniority', store=True)
    seniority_years = fields.Integer('Année', compute='get_seniority', store=True)
    deposit_date = fields.Date('Date dépôt', help="Date de dépôt de la lettre de démission")
    date_return_last_holidays = fields.Date('Date de retour dernier congé', compute='get_employee_info', store=True,
                                            help="Date de retour du dernier congé")
    gross_salary_leave = fields.Integer('BRUT congé', compute='get_gross_salary_leave', store=True,
                                        help='Cumul des BRUT depuis le dernier congé')
    estimated_departure_date = fields.Date('Date sortie prévisionnelle', compute='compute_estimated_departure_date',
                                           help="Date de sortie si l'employé effectue son préavis dans les normes")
    notice_given = fields.Integer("Préavis effectué", compute='compute_estimated_departure_date', store=True,
                                  help="Préavis effectué en fonction de la date de dépôt de la lettre de démission "
                                       "et de la date de sortie effective.")
    notice_not_given = fields.Integer("Préavis non effectué", compute='compute_estimated_departure_date',
                                      store=True, help="Différence entre 60 et le préavis effectué.Il permet de savoir"
                                                       " si l'employé doit rembourser à l'entreprise.")
    total_indemnity = fields.Integer('Total indemnité', default=0, compute='get_indemnity',
                                     help="Le cumul des indemnités")
    taxable_indemnity = fields.Integer('Indemnité imposable', default=0, compute='get_indemnity',
                                       help="La part de l'indemnité qui est imposable")
    spreading_period = fields.Integer('Période étalement')
    not_taxable_indemnity = fields.Integer('Indemnité non imposable', default=0, compute='get_indemnity',
                                           help="La part de l'indemnité qui est non imposable")
    employee_id = fields.Many2one('hr.employee', 'Employé', required=True, ondelette='cascade',default=_get_employee_id)
    contract_id = fields.Many2one('hr.contract', 'Contrat', required=False, compute='get_employee_info', store=True)
    motif_fin_contract_id = fields.Many2one('hr.employee.motif.cloture', 'Motif du départ',
                                            help="Utilisé pour le calcul des indemnités.")
    state = fields.Selection([('draft', 'Bouillion'), ('validate', 'Validé')], string='Etat', default='draft',
                             track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Compagnie', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    last_salary_line_ids = fields.One2many('hr_payroll_ci.last_salary_line', 'balance_any_account_id',
                                           'Derniers bulletins')
    salary_elements_ids = fields.One2many('hr_payroll_ci.salary_elements', 'balance_any_account_id',
                                          'Elements du salaire')
    balance_any_account_line_ids = fields.One2many('hr_payroll_ci.balance_any_account_line', 'balance_any_account_id',
                                                   'Recapitulatif')
    allowances_ids = fields.One2many('hr_payroll_ci.allowances', 'balance_any_account_id', 'Indemnités')

    @api.onchange('employee_id')
    def get_employee_info(self):
        if self.employee_id:
            hiring_date = self.employee_id.start_date
            self.hiring_date = hiring_date
            self.date_return_last_holidays = self.employee_id.date_return_last_holidays
            self.motif_fin_contract_id = self.employee_id.motif_fin_contract_id
            self.contract_id = self.employee_id.contract_id

            name = 'SOLDE DE TOUT COMPTE ' + self.employee_id.name + ' ' + self.employee_id.first_name + ' (' + \
                   self.employee_id.identification_id + ')'
            self.name = name
            contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')]
                                                      , limit=1)
            if contract:
                self.contract_id = contract.id
            else:
                self.contract_id = False
        else:
            self.motif_fin_contract_id = False

    @api.onchange('hiring_date', 'end_date')
    @api.depends('hiring_date', 'end_date')
    def get_seniority(self):
        if self.hiring_date and self.end_date:
            seniority_total = relativedelta.relativedelta(self.end_date, self.hiring_date)
            self.seniority_days = seniority_total.days + 1
            self.seniority_months = seniority_total.months
            self.seniority_years = seniority_total.years
            self.seniority = seniority_total.days + seniority_total.months * 30 + seniority_total.years * 360 + 1

    @api.onchange('salary_elements_ids')
    @api.depends('salary_elements_ids')
    def get_sum_salary_elements(self):
        if self.salary_elements_ids:
            self.sum_salary_elements = sum([x.amount for x in self.salary_elements_ids])
        else:
            self.sum_salary_elements = 0

    @api.onchange('allowances_ids')
    @api.depends('allowances_ids')
    def get_indemnity(self):
        if self.allowances_ids:
            total_indemnity = sum([x.amount for x in self.allowances_ids])
            self.total_indemnity = total_indemnity
            self.not_taxable_indemnity = ceil(total_indemnity / 2)
            self.taxable_indemnity = total_indemnity - self.not_taxable_indemnity
        else:
            self.total_indemnity = 0
            self.not_taxable_indemnity = 0
            self.taxable_indemnity = 0

    @api.onchange('last_salary_line_ids')
    @api.depends('last_salary_line_ids')
    def get_gross_salary_leave(self):
        if self.last_salary_line_ids:
            last_payslip = self.last_salary_line_ids.filtered(lambda d: d.order == 1)
            self.gross_salary_leave = last_payslip.payslip_id.gross_salary_leave
            print('L128 gross_salary_leave ', self.gross_salary_leave)
        else:
            #chercher le dernier bulletin et recuperer le brut conge
            payslips = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'done')
                                                      ], order='date_from desc', limit=1)
            if payslips:
                self.gross_salary_leave = payslips.gross_salary_leave
            else:
                #recuperer le solde conge car nouvelle installation
                self.gross_salary_leave = self.employee_id.leave_balance

    def generate_data(self):
        if self.employee_id:
            calendar_days_off = 0
            if self.deposit_date > self.end_date:
                raise Warning(_("La date de départ effective doit être supérieur à la date de dépôt de la "
                                "lettre de démission. Merci de faire les corrections nécessaires."))

            payslips = self.env['hr.payslip'].search(
                [('employee_id', '=', self.employee_id.id), ('state', '=', 'done')],
                order='date_from desc', limit=12)
            if payslips:
                res_payslip = []
                cpt = 0
                for payslip in payslips:
                    cpt += 1
                    vals_payslip = {
                        'order': cpt,
                        'name': payslip.name,
                        'payslip_id': payslip.id,
                        'balance_any_account_id': self.id
                    }
                    res_payslip.append(vals_payslip)
                self.last_salary_line_ids.unlink()
                self.env['hr_payroll_ci.last_salary_line'].create(res_payslip)

            total_gross = 0
            for payslip in self.last_salary_line_ids:
                total_gross += payslip.gross_amount
            if self.other_indemnity > 0:
                total_gross += self.other_indemnity
            self.total_gross = total_gross
            self.average_gross = ceil(total_gross / 12)

            if self.contract_id:
                res_contract = []
                vals = {
                    'balance_any_account_id': self.id,
                    'name': 'Salaire catégoriel',
                    'amount': self.contract_id.wage
                }
                res_contract.append(vals)
                vals = {
                    'balance_any_account_id': self.id,
                    'name': 'Sursalaire',
                    'amount': self.contract_id.sursalaire
                }
                res_contract.append(vals)
                self.employee_id._get_seniority()
                if self.employee_id.seniority_employee >= 2:
                    vals = {
                        'balance_any_account_id': self.id,
                        'name': "Primes d'ancienneté",
                        'amount': self.contract_id.wage * 0.01 * min(self.employee_id.seniority_employee, 25)
                    }
                    res_contract.append(vals)

                for line in self.contract_id.hr_payroll_prime_ids:
                    vals = {
                        'balance_any_account_id': self.id,
                        'name': line.prime_id.name,
                        'prime_id': line.prime_id.id,
                        'amount': line.montant_prime
                    }
                    res_contract.append(vals)
                self.salary_elements_ids.unlink()
                self.env['hr_payroll_ci.salary_elements'].create(res_contract)

            if self.motif_fin_contract_id:
                if self.motif_fin_contract_id.indemnity:
                    res_indemnity = []
                    if 360 <= self.seniority:
                        seniority = min(self.seniority, 1800)
                        val_indemnity = {
                            'balance_any_account_id': self.id,
                            'name': 'Ancienneté de 1 à 5 ans',
                            'amount': ceil(self.average_gross * 0.30 * (seniority / 360))
                        }
                        res_indemnity.append(val_indemnity)
                    if 1800 < self.seniority:
                        seniority = min(self.seniority, 3600) - 1800
                        val_indemnity = {
                            'balance_any_account_id': self.id,
                            'name': 'Ancienneté de 5 à 10 ans',
                            'amount': ceil(self.average_gross * 0.35 * (seniority / 360))
                        }
                        res_indemnity.append(val_indemnity)
                    if 3600 < self.seniority:
                        seniority = self.seniority - 3600
                        val_indemnity = {
                            'balance_any_account_id': self.id,
                            'name': 'Ancienneté supérieur à 10 ans',
                            'amount': ceil(self.average_gross * 0.40 * (seniority / 360))
                        }
                        res_indemnity.append(val_indemnity)

                    if res_indemnity:
                        self.allowances_ids.unlink()
                        self.env['hr_payroll_ci.allowances'].create(res_indemnity)
                else:
                    pass

            # Recapitulate

            # Préavis effectué
            res_recap = []
            bonus_transport = self.company_id.bonus_transport
            notice_paid = self.notice_given / 3
            vals_recap = {
                'balance_any_account_id': self.id,
                'name': "Temps de recherche d'emploi / préavis effectués (" + str(int(notice_paid)) + " jours)",
                'amount': round((self.notice_given / 3) * ((self.sum_salary_elements - bonus_transport) / 30))
            }
            res_recap.append(vals_recap)

            # Préavis non effectué
            vals_recap = {
                'balance_any_account_id': self.id,
                'name': 'Préavis non effectués (' + str(self.notice_not_given) + ' jours)',
                'amount': round(self.notice_not_given * (self.sum_salary_elements / 30)) * (-1)
            }
            res_recap.append(vals_recap)

            # calcul des indemnités de congés
            if self.end_date and self.date_return_last_holidays:
                duration_presence = relativedelta.relativedelta(self.end_date, self.date_return_last_holidays)
                days_presence = duration_presence.years * 360 + duration_presence.months * 30 + duration_presence.days
                facteur = self.company_id.number_holidays_locaux if self.employee_id.nature_employe == 'local' \
                    else self.company_id.number_holidays_expat
                acquired_leave = facteur * days_presence / 30
                # Prise en compte des jours supplémentaires liés à une décoration"
                if self.medal_leave > 0:
                    acquired_leave += self.medal_leave
                # determination des jours suplémentaires liés à l'ancienneté
                seniority_in_years = self.seniority_years
                if 5 <= seniority_in_years < 10:
                    acquired_leave += 1
                elif 10 <= seniority_in_years < 15:
                    acquired_leave += 2
                elif 15 <= seniority_in_years < 20:
                    acquired_leave += 3
                elif 20 <= seniority_in_years < 25:
                    acquired_leave += 5
                elif 25 <= seniority_in_years < 30:
                    acquired_leave += 7
                elif seniority_in_years >= 30:
                    acquired_leave += 8
                else:
                    pass
                if self.employee_id.gender == 'female':
                    if self.employee_id.age < 21:
                        acquired_leave += 2 * self.employee_id.children
                    else:
                        if self.employee_id.children >= 4:
                            acquired_leave += 2 * (self.employee_id.children - 3)
                calendar_days_off = round(round(acquired_leave) + round(acquired_leave) / 6)
                average_holiday_salary = ceil(self.gross_salary_leave / days_presence)
                vals_recap = {
                    'balance_any_account_id': self.id,
                    'name': 'Allocation congés (' + str(calendar_days_off) + ' jours)',
                    'amount': round(average_holiday_salary * calendar_days_off)
                }
                res_recap.append(vals_recap)

            # Calcul de la gratification
            if self.end_date:
                year = self.end_date.year
                first_day_year = str(year) + '-01-01'
                first_day_year = datetime.strptime(first_day_year, '%Y-%m-%d')
                delta_days = relativedelta.relativedelta(self.end_date, first_day_year)
                delta_days = delta_days.months * 30 + delta_days.days
                quotient_days_bonus = ceil(delta_days / 360)
                print('L308 quotient_days_bonus ', quotient_days_bonus)
                vals_recap = {
                    'balance_any_account_id': self.id,
                    'name': 'Gratification (' + str(delta_days) + ' jours)',
                    'amount': round(self.sum_salary_elements * quotient_days_bonus)
                }
                res_recap.append(vals_recap)
                print('L315 calendar_days_off ', calendar_days_off)
                quotient_days_bonus = calendar_days_off / 360
                print('L316 quotient_days_bonus ', quotient_days_bonus)
                vals_recap = {
                    'balance_any_account_id': self.id,
                    'name': 'Gratification/Congé (' + str(calendar_days_off) + ' jours)',
                    'amount': round(self.sum_salary_elements * quotient_days_bonus)
                }
                res_recap.append(vals_recap)

                # Calcul du Treizieme mois
                quotient_days_bonus = ceil(delta_days / 360)
                vals_recap = {
                    'balance_any_account_id': self.id,
                    'name': 'Treizième mois (' + str(delta_days) + ' jours)',
                    'amount': round(self.sum_salary_elements * quotient_days_bonus)
                }
                res_recap.append(vals_recap)
                quotient_days_bonus = calendar_days_off / 360
                vals_recap = {
                    'balance_any_account_id': self.id,
                    'name': 'Treizième mois/ Congé (' + str(calendar_days_off) + ' jours)',
                    'amount': round(self.sum_salary_elements * quotient_days_bonus)
                }
                res_recap.append(vals_recap)

                # Transport non imposable recherche emploi
                vals_recap = {
                    'balance_any_account_id': self.id,
                    'name': "Transport non imposable /Recherche d'emploi (" + str(int(notice_paid)) + " jours)",
                    'amount': round(notice_paid * bonus_transport / 30)
                }
                res_recap.append(vals_recap)

                # Congés non pris
                # leave_not_taken = self.env['hr_cnce.save_stock_holiday'].search(
                #     [('employee_id', '=', self.employee_id.id), ('name', '=', str(self.end_date.year))]).number_days
                # if not leave_not_taken:
                #     leave_not_taken = ceil(self.employee_id.remaining_leaves)
                # vals_recap = {
                #     'balance_any_account_id': self.id,
                #     'name': "Congés non pris (" + str(leave_not_taken) + " jours)",
                #     'amount': round(((self.sum_salary_elements - bonus_transport) / 30) * leave_not_taken)
                # }
                # res_recap.append(vals_recap)

                # Période etalement
                month = self.end_date.month

                first_day_month = str(year) + '-' + str(month) + '-01'
                first_day_month = datetime.strptime(first_day_month, '%Y-%m-%d')
                days_worked = relativedelta.relativedelta(self.end_date, first_day_month)
                self.spreading_period = notice_paid + days_worked.days + calendar_days_off

                # Calcul ITS

            if self.allowances_ids:
                self.allowances_ids.unlink()
            if self.last_salary_line_ids:
                self.last_salary_line_ids.unlink()
            self.balance_any_account_line_ids.unlink()
            self.env['hr_payroll_ci.balance_any_account_line'].create(res_recap)
        else:
            raise Warning(_("Vous devez choisir un employé avant l'exécution de cette action."))

    @api.depends('deposit_date', 'end_date')
    def compute_estimated_departure_date(self):
        if self.deposit_date:
            self.estimated_departure_date = self.deposit_date + relativedelta.relativedelta(days=90)
            if self.end_date:
                notice_given = (self.end_date - self.deposit_date)
                self.notice_given = notice_given.days
                if notice_given.days > 60:
                    self.notice_not_given = 0
                else:
                    self.notice_not_given = 60 - notice_given.days
        else:
            self.estimated_departure_date = False

    def action_done(self):
        balances = self.env['hr_payroll_ci.balance_any_account'].search([('state', '=', 'validate')])
        for rec in balances:
            if rec.employee_id.id == self.employee_id.id:
                raise Warning("Un employé n'a droit qu'à un seul solde de tout compte valide!")
            else:
                pass
        self.state = 'validate'


class PayrollLastSalary(models.Model):
    _name = 'hr_payroll_ci.last_salary_line'
    _description = '12 derniers salaires'

    name = fields.Char('Référence')
    order = fields.Integer('N° ordre', default=0)
    period = fields.Char('Période', compute='get_data', strore=True)
    gross_amount = fields.Integer('Montant (BRUT)', compute='get_data', store=True)
    payslip_id = fields.Many2one('hr.payslip', 'Bulletin')
    balance_any_account_id = fields.Many2one('hr_payroll_ci.balance_any_account', 'Solde de tout compte',
                                             ondelette='cascade')

    @api.depends('payslip_id')
    def get_data(self):
        if self.payslip_id:
            gross_amount = 0
            for line in self.payslip_id.line_ids:
                if line.code == 'BRUT':
                    gross_amount = line.total
                    break
            self.gross_amount = gross_amount
        else:
            raise Warning(_("Vous devez définir le bulletin avant d'effectuer cette action."))


class PayrollSalaryElements(models.Model):
    _name = 'hr_payroll_ci.salary_elements'
    _description = "Les elements du salaire"

    name = fields.Char('Libellé')
    prime_id = fields.Many2one('hr.payroll.prime', 'Rubrique')
    rule_id = fields.Many2one('hr.salary.rule', 'Règle', compute='get_rule', store=True)
    amount = fields.Integer('Montant')
    balance_any_account_id = fields.Many2one('hr_payroll_ci.balance_any_account', 'Solde de tout compte',
                                             ondelette='cascade')

    @api.depends('prime_id')
    def get_rule(self):
        for rec in self:
            if rec.prime_id:
                rule_rec = self.env['hr.salary.rule'].search([('code', '=', rec.prime_id.code)], limit=1)
                rec.rule_id = rule_rec.id


class PayrollAllowances(models.Model):
    _name = 'hr_payroll_ci.allowances'
    _description = "Les indemnités du solde de tout compte"

    name = fields.Char('Libellé')
    amount = fields.Integer('Montant')
    balance_any_account_id = fields.Many2one('hr_payroll_ci.balance_any_account', 'Solde de tout compte',
                                             ondelette='cascade')


class PayrollBalanceAnyAccountLine(models.Model):
    _name = 'hr_payroll_ci.balance_any_account_line'
    _description = "Ligne des soldes de tout compte"

    name = fields.Char('Libellé')
    amount = fields.Integer('Montant')
    balance_any_account_id = fields.Many2one('hr_payroll_ci.balance_any_account', 'Solde de tout compte',
                                             ondelette='cascade')
