# -*- coding: utf-8 -*-
##############################################################################
##############################################################################


from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _getTotalCGRAE(self):
        for res in self:
            total = res.tx_cgrae_employee + res.tx_cgrae_employer
            res.tx_cgrae_total = total

    general_manager_id = fields.Many2one('hr.employee', 'Directeur Général', required=False)
    direction_general_note = fields.Text("Mot de la direction général", required=False)
    hr_manager_id = fields.Many2one('hr.employee', 'Directeur des Ressources Humaines', required=True)
    days_before_holidays = fields.Integer(string="Alerte avant congés (Jours)")
    days_after_holidays = fields.Integer(string="Alerte après congés (Jours)")
    first_alert_retraite = fields.Integer(string="Première alerte depart retraite (Mois)", readonly=False)
    second_alert_retraite = fields.Integer(string="Deuxième alerte depart retraite (Mois)", readonly=False)
    first_alert_real_planning = fields.Integer(string="Première alerte planning réel (Jours)", readonly=False)
    second_alert_real_planning = fields.Integer(string="Deuxième alerte planning réel (Jours)", readonly=False)
    signature_drh = fields.Binary("Singature du DRH", required=False)
    account_salary_id = fields.Many2one("account.account", "Compte utilisé pour la masse salariale", required=False)
    alert_trial_contract_expiry = fields.Integer(string="Alerte de fin de contrat essai (Jours)", default=0)
    alert_contract_expiry_cadre = fields.Integer(string="Alerte de fin de contrat pour les cadres (Jours)", default=0)
    alert_contract_expiry_non_cadre = fields.Integer(string="Alerte de fin de contrat pour les non cadres (Jours)",
                                                     default=0)
    alert_receiver_one = fields.Many2one("hr.employee", "Responsale personnel")
    alert_receiver_two = fields.Many2one("hr.employee", "Responsable Paie")
    sigle = fields.Char(string="Sigle de la société")
    date_start_work_hour = fields.Char("Heure Début de travail", default='07H30')

    days_before_birthday = fields.Integer("Nombre de jours avant la date d'anniversaire", default=0, readonly=False)
    rate_ce_local = fields.Float("Taux CE employés locaux", default=0)
    rate_ce_expat = fields.Float("Taux CE employés expat", default=11.5)
    rate_ce_agricole = fields.Float("Taux employeur Régime agricole", default=2)
    rate_its = fields.Float("Taux ITS", default=1.2)
    acronym = fields.Char('Sigle')
    legal_status = fields.Char('Forme', help="S.A., S.A.R.L., S.N.C., S.C.S...")
    account_number = fields.Char('Numéro de compte', help="Utilisé pour la déclaration de l'ITS")
    activity_code = fields.Char('Code Activ.', help="Code Activité. Utilisé au niveau de la déclaration CNPS")
    activity_label = fields.Char('Activité', help="Activité. Utilisé dans la déclaration FDFP")
    profession = fields.Char('Profession', help="Profession de la société. Utilisé dans l'Etat 301")
    tax_base_service = fields.Char("Service des impots", help="Service des impôts en charge de receptionner les "
                                                              "déclarations de l'entreprise.")
    address = fields.Char('Adresse postale')

    retirement_age = fields.Integer("Age de départ à la retraite (ans)")
    establishment_code = fields.Char('Code Etab.', help="Code Établissement. Utilisé au niveau de la déclaration CNPS")
    num_cnps = fields.Char("Numéro CNPS", size=124, required=True)
    num_contribuable = fields.Char("Numéro Contribuable", size=128, required=True)
    system_implementation_date = fields.Date('Date de mise en place du système',
                                             help="Cette date permettra de tenir compte de certaines informations "
                                                  "antérieur telle que le solde antérieur des congés dans les calculs")
    tx_cgrae_employee = fields.Float("Taux CGRAE employé (%)", default=8.33)
    tx_cgrae_employer = fields.Float("Taux CGRAE Employeur(%)", default=16.67)
    tx_cgrae_total = fields.Float("Total taux CGRAE", compute="_getTotalCGRAE")
    bonus_transport = fields.Integer('Primes de transport', help="Renseignez la prime de transport non imposable selon"
                                                                 " la législation en vigueur")
    alert_send_payslip = fields.Integer(string="Alerte d'envoi de fiches de paie à compter d'aujourd'hui", default=0)