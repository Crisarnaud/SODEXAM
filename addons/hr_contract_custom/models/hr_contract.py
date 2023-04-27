# -*- coding: utf-8 -*-

import time
from odoo import api, fields, osv, exceptions, models, exceptions
from datetime import datetime
from odoo.tools.translate import _
import xlrd
from odoo.exceptions import ValidationError

from dateutil.relativedelta import relativedelta
from odoo.osv import expression


class HrCatgeryContract (models.Model):
    _name = "hr.category.contract"
    _description = "Categorie de contrat"

    name = fields.Char ("Libelle ", required=True)
    code = fields.Char ('Code', required=True, size=2)
    sequence = fields.Integer ('Séquence', required=True)
    delai_notif_fin = fields.Integer ("Fin contrat (jours)", required=False)
    delai_notif_essai = fields.Integer ("Fin période d'essai (jours)", required=False)
    description = fields.Text ("Description", required=False)


class HrContract (models.Model):
    _inherit = "hr.contract"

    @api.constrains ('employee_id', 'state', 'kanban_state', 'date_start', 'date_end')
    def _check_current_contract(self):
        """ Two contracts in state [incoming | open | close] cannot overlap """
        for contract in self.filtered (lambda c: (c.state not in ['draft', 'cancel',
                                                                  'close'] or c.state == 'draft' and c.kanban_state == 'done') and c.employee_id):
            domain = [
                ('id', '!=', contract.id),
                ('employee_id', '=', contract.employee_id.id),
                '|',
                ('state', 'in', ['open', 'availability']),
                '&',
                ('state', '=', 'draft'),
                ('kanban_state', '=', 'done')  # replaces incoming
            ]

            if not contract.date_end:
                start_domain = []
                end_domain = ['|', ('date_end', '>=', contract.date_start), ('date_end', '=', False)]
            else:
                start_domain = [('date_start', '<=', contract.date_end)]
                end_domain = ['|', ('date_end', '>', contract.date_start), ('date_end', '=', False)]

            domain = expression.AND ([domain, start_domain, end_domain])
            if self.search_count (domain):
                raise ValidationError (_ (
                    "un salarié ne peut avoir qu'un seul contrat à la fois. (Hors projets de contrats, annulés et expirés)"))

    def _default_employee_id(self):
        for employee in self:
            return employee.employee_id.name + '' + employee.employee_id.first_name

    # @api.onchange ('categorie_salariale_id')
    # def categ_sal(self):
    #     record_ids = self.env['hr.employee'].search ([('id', '=', self.employee_id.id)])
    #     record_ids.write ({'categorie_salariale_id': self.categorie_salariale_id.id })
    #
    # @api.onchange ('category_id')
    # def categ_sal(self):
    #     record_ids = self.env['hr.employee'].search ([('id', '=', self.employee_id.id)])
    #     record_ids.write ({'category_contract_id': self.category_id.id
    #                        })

    def cron_send_mail(self):
        """
        Fonction verifiant la date de fin de contrat et de fin de periode d'essai ensuite envois un mail de notification
        aux différents responsables de la société
        :return:
        """
        today = datetime.today ()
        config_rc = self.env['res.company'].search ([], limit=1)
        contracts = self.env['hr.contract'].search (['|', '|',
                                                     ('trial_date_end', '=',
                                                      str (today + relativedelta (
                                                          days=config_rc.alert_trial_contract_expiry))[:10]),
                                                     ('date_end', '=',
                                                      str (today + relativedelta (
                                                          days=config_rc.alert_contract_expiry_cadre))[:10]),
                                                     ('date_end', '=',
                                                      str (today + relativedelta (
                                                          days=config_rc.alert_contract_expiry_non_cadre))[:10]),
                                                     ('state', '=', 'open')])
        if contracts:
            for contract in contracts:
                if contract.trial_date_end:
                    email_template_id = self.env.ref ('hr_contract_custom.template_alert_email_trial_contract').id
                elif contract.date_end:
                    email_template_id = self.env.ref ('hr_contract_custom."cron_email_contract_template"').id
                email_template = self.env['mail.template'].browse (email_template_id)
                email_template.send_mail (contract.id, force_send=True)

    # @api.onchange ('notify_model_id', 'date')
    # def compute_notification(self):
    #     res = []
    #     self.notification_lines_ids = []
    #     if self.notify_model_id:
    #         if self.date_end:
    #             date = fields.Datetime.from_string (self.date_end)
    #             data = self.notify_model_id.getNotifLine (date)
    #             self.notification_lines_ids = data

    @api.onchange ('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.job_id = self.employee_id.job_id
            self.department_id = self.employee_id.department_id
            self.date_start = self.employee_id.start_date

    def calcul_anciennete_actuel(self):
        """calcul de l'ancienneté"""
        self.ensure_one ()
        this_date = today = datetime.today ()
        start_date = fields.Datetime.from_string (self.employee_id.start_date)
        if self.date_end:
            end_date = fields.Datetime.from_string (self.date_end)
            this_date = min (today, end_date)
        tmp = relativedelta (this_date, start_date) + relativedelta (months=+self.mois_report, years=+ self.an_report)
        anciennete = {
            'year_old': tmp.years,
            'month_old': tmp.months,
        }
        return anciennete

    def _get_anciennete(self):
        res = {}
        anciennete = self.calcul_anciennete_actuel ()
        if anciennete:
            self.an_anciennete = anciennete['year_old']
            self.mois_anciennete = anciennete['month_old']

    expatried = fields.Boolean ('Expatrié', default=False)
    an_report = fields.Integer ('Report Ancienneté (Année)', size=2)
    mois_report = fields.Integer ('Mois report')
    an_anciennete = fields.Integer ("Nombre d'année", compute='_get_anciennete')
    mois_anciennete = fields.Integer ('Nombre de mois', compute='_get_anciennete')
    anne_anc = fields.Integer ('Ancienneté (Année)')
    sursalaire = fields.Integer ('Sursalaire', required=False, store=True)
    hr_convention_id = fields.Many2one ('hr.convention', "Convention", required=False)
    hr_secteur_id = fields.Many2one ('hr.secteur.activite', "Secteur d'activité", required=False)
    categorie_salariale_id = fields.Many2one ('hr.categorie.salariale', 'Catégorie salariale', required=False,
                                              readonly=False)
    hr_payroll_prime_ids = fields.One2many ("hr.payroll.prime.montant", 'contract_id', "Primes")
    type_ended = fields.Selection ([('licenced', 'Licencement'), ('hard_licenced', 'Licencement faute grave'),
                                    ('ended', 'Fin de contrat')], 'Type de clôture', index=True)
    description_cloture = fields.Text ("Motif de Clôture")
    wage = fields.Float ('Salaire de base', required=True, readonly=False, compute="on_change_categorie_salariale_id")
    # notify_model_id = fields.Many2one('notify.model', 'Modèle de notification', required=False)
    # notif_ids = fields.One2many('notif.line', 'res_id', 'lignes')
    model_contract_id = fields.Many2one ("hr.model.contract", "Modèle de contrat", required=False)
    state = fields.Selection (selection_add=[('availability', 'En disponibilité')])
    contract_availability_ids = fields.One2many ('hr.contract_availability', 'contract_id',
                                                 'Historique des mises en diponibilite')
    notification_lines_ids = fields.One2many ('hr.contract.notification.line', 'contract_id',
                                              "Les dates de notification")
    category_id = fields.Many2one ('hr.category.contract', 'Catégorie de contrat', required=False)
    contract_id = fields.Many2one ('hr.contract', 'Catégorie de contrat', required=False)
    date_noty_fin_contract = fields.Date ("Date de notification de fin")
    date_noty_fin_essai = fields.Date ('Date de nofitication de fin essai')
    salaire_cgrae = fields.Float ("Salaire de base CGARE")
    contract_type_id = fields.Many2one ('hr.type.contract', 'Type de contrat', required=False)
    employee_id = fields.Many2one ('hr.employee', 'Employé', default=_default_employee_id)

    @api.onchange ("model_contract_id")
    @api.depends ("model_contract_id")
    def onChangeContractModel(self):
        self.job_id = self.model_contract_id.titre_poste
        self.struct_id = self.model_contract_id.structure_salariale
        self.hr_convention_id = self.model_contract_id.convention_id
        self.hr_secteur_id = self.model_contract_id.secteur_activite_id
        self.categorie_salariale_id = self.model_contract_id.categorie_salariale
        self.contract_type_id = self.model_contract_id.type_contract
        primes = [(5, 0, 0)]
        for prime in self.model_contract_id.prime_ids:
            prime_values = {
                'prime_id': prime.prime_id.id,
                'montant_prime': prime.montant_prime,
                'contract_id': self.id,

            }
            primes.append ((0, 0, prime_values))
        self.hr_payroll_prime_ids = primes

    # @api.onchange('notify_model_id')
    # def compute_notification(self):
    #     self.ensure_one()
    #     notif_model = self.env['notif.line']
    #     if self.date_end:
    #         date = fields.Datetime.from_string(self.date_end)
    #         params = self._context.get('params')
    #         for line in self.notify_model_id.line_ids:
    #             notif_model.generate_notification_line(self.name, self.id, line, date)

    def validate_contract(self):
        return self.write ({'state': 'open'})

    def closing_contract(self):
        view_id = self.env['ir.model.data'].get_object_reference ('hr_contract_custom',
                                                                  'hr_contract_closed_form_view')
        return {
            'name': _ ("Clôture de contrat"),
            'view_mode': 'form',
            'view_id': view_id[1],
            'view_type': 'form',
            'res_model': 'hr.contract.closed',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': self._context,
        }

    def action_cancel(self):
        return self.write ({'state': 'cancel'})

    @api.onchange ("hr_convention_id")
    def on_change_convention_id(self):
        if self.hr_convention_id:
            return {'domain': {'hr_secteur_id': [('hr_convention_id', '=', self.hr_convention_id.id)]}}
        else:
            return {'domain': {'hr_secteur_id': [('hr_convention_id', '=', False)]}}

    @api.onchange ("hr_secteur_id")
    def on_change_secteur_id(self):
        if self.hr_secteur_id:
            return {'domain': {'categorie_salariale_id': [('hr_secteur_activite_id', '=', self.hr_secteur_id.id)]}}
        else:
            return {'domain': {'categorie_salariale_id': [('hr_secteur_activite_id', '=', False)]}}

    @api.depends ('categorie_salariale_id')
    def on_change_categorie_salariale_id(self):
        for cat in self:
            if cat.categorie_salariale_id:
                cat.wage = cat.categorie_salariale_id.salaire_base
                cat.employee_id.categorie_salariale_id = cat.categorie_salariale_id

    @api.depends ('category_id')
    def on_change_category_id(self):
        if self.category_id:
            self.employee_id.category_contract_id = self.category_id

    def define_date_return_availability(self):
        if self.state == 'availability':
            for record in self.contract_availability_ids:
                if not record.return_date_availability:
                    record.return_date_availability = fields.Date.today ()
            self.state = 'open'

    # def import_primes(self):
    #     for data_file in self.hr_payroll_prime_ids:
    #         file_name = data_file.name.lower()
    #         try:
    #             if file_name.strip().endswith('.csv') or file_name.strip().endswith('.xlsx'):
    #                 statement = False
    #                 if file_name.strip().endswith('.csv'):
    #                     keys = ['prime_id', 'montant_prime']
    #                     try:
    #                         csv_data = base64.b64decode(data_file.datas)
    #                         data_file = io.StringIO(csv_data.decode("utf-8"))
    #                         data_file.seek(0)
    #                         file_reader = []
    #                         values = {}
    #                         csv_reader = csv.reader(data_file, delimiter=',')
    #                         file_reader.extend(csv_reader)
    #                     except:
    #                         raise UserError(("Invalid file!"))
    #                     vals_list = []
    #                     date = False
    #                     for i in range(len(file_reader)):
    #                         field = list(map(str, file_reader[i]))
    #                         values = dict(zip(keys, field))
    #                         if values:
    #                             if i == 0:
    #                                 continue
    #                             else:
    #                                 if not date:
    #                                     date = field[0]
    #                                 values.update({
    #                                     'prime_id': field[0],
    #                                     'montant_prime': field[1]
    #                                 })
    #                                 vals_list.append((0, 0, values))
    #                     statement_vals = {
    #                         'name': 'Statement Of ' + str(datetime.today().date()),
    #                         'journal_id': self.env.context.get('active_id'),
    #                         'line_ids': vals_list
    #                     }
    #                     if len(vals_list) != 0:
    #                         statement = self.create_statement(statement_vals)
    #                 elif file_name.strip().endswith('.xlsx'):
    #                     try:
    #                         fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    #                         fp.write(binascii.a2b_base64(data_file.datas))
    #                         fp.seek(0)
    #                         values = {}
    #                         workbook = xlrd.open_workbook(fp.name)
    #                         sheet = workbook.sheet_by_index(0)
    #                     except:
    #                         raise UserError(("Invalid file!"))
    #                     vals_list = []
    #                     for row_no in range(sheet.nrows):
    #                         val = {}
    #                         values = {}
    #                         if row_no <= 0:
    #                             fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
    #                         else:
    #                             line = list(map(
    #                                 lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(
    #                                     row.value), sheet.row(row_no)))
    #                             values.update({
    #                                 'date': line[0],
    #                                 'payment_ref': line[1],
    #                                 'ref': line[2],
    #                                 'partner_id': self.get_partner(line[3]),
    #                                 'amount': line[4],
    #                                 'currency_id': self.get_currency(line[5])
    #                             })
    #                             vals_list.append((0, 0, values))
    #                     statement_vals = {
    #                         'name': 'Statement Of ' + str(datetime.today().date()),
    #                         'journal_id': self.env.context.get('active_id'),
    #                         'line_ids': vals_list
    #                     }
    #                     if len(vals_list) != 0:
    #                         statement = self.create_statement(statement_vals)
    #                 if statement:
    #                     return {
    #                         'type': 'ir.actions.act_window',
    #                         'res_model': 'hr.contract',
    #                         'view_mode': 'form',
    #                         'res_id': statement.id,
    #                         'views': [(False, 'form')],
    #                     }
    #             else:
    #                 raise ValidationError(("Unsupported File Type"))
    #         except Exception as e:
    #             raise ValidationError(("Please upload in specified format ! \n"
    #                                    "date, payment reference, reference, partner, amount, currency !"))


class HrContractAvailability (models.Model):
    _name = 'hr.contract_availability'
    _description = "Mise en disponibilite"

    def _default_contract_id(self):
        for contract in self:
            return contract.contract_id.id

    name = fields.Char ('Référence')
    start_date_availability = fields.Date ('Date de début de mis en disponibilité' ,default=datetime.today ())
    previsional_end_date_availability = fields.Date ('Date previsionnelle de fin', default=datetime.today ())
    return_date_availability = fields.Date ('Date de fin de mis en disponibilité', default=datetime.today ())
    contract_id = fields.Many2one ('hr.contract', 'Contrat')

    @api.model
    def create(self, vals):
        if 'contract_id' in vals:
            contracts = self.search ([('contract_id', '=', vals['contract_id'])])
            for contract in contracts:
                if not contract.return_date_availability:
                    raise exceptions.ValidationError (
                        _ ('Vous ne pouvez pas créer un nouvel enregistrement sans notifier'
                           ' le retour de la précédente mise en disponibilité'))
        record = super (HrContractAvailability, self).create (vals)
        return record

    def cron_return_delay_alert_on_availability(self):
        """
        Fonction permettant d'envoyer une alerte aux responsables de la société en cas de retard de retour de mise
        en disponibilité
        :return:
        """
        today = datetime.today ()
        for line in self.search ([('previsional_end_date_availability', '<', str (today)[:10])]):
            if not line.return_date_availability:
                email_template_id = self.env.ref ('hr_contract_custom.template_return_delay_alert_on_availability').id
                email_template = self.env['mail.template'].browse (email_template_id)
                email_template.send_mail (line.id, force_send=True)


class HrContractNoitificationLine (models.Model):
    _name = 'hr.contract.notification.line'
    _description = "Ligne de notification de contrat"

    date_notification = fields.Date ("Date de notification", required=True)
    contract_id = fields.Many2one ('hr.contract', 'Contrat', required=False)
