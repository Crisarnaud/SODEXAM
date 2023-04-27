# -*- encoding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2012 Veone - support.veone.net
# Author: Veone
#
# Fichier du module hr_emprunt
# ##############################################################################  -->
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _
import logging

_logger = logging.getLogger (__name__)

Type_employee = [('h', 'Horaire'), ('j', 'Journalier'), ('m', 'Mensuel')]


class HrEmployee (models.Model):
    _inherit = 'hr.employee'
    _order = 'identification_id'

    @api.depends ('marital', 'child_in_charge')
    def _get_part_igr(self):
        """
        fonction permettant de calculer la part igr de l'employé
        """
        for rec in self:
            result = 0
            if rec.marital:
                t1 = rec.marital
                B38 = t1[0]
                B39 = rec.child_in_charge

                if (B38 == "s") or (B38 == "d"):
                    if B39 == 0:
                        result = 1
                    elif (1.5 + B39 * 0.5) > 5:
                        result = 5
                    else:
                        result = 1.5 + B39 * 0.5
                else:
                    if B38 == "m":
                        if B39 == 0:
                            result = 2
                        else:
                            if (2 + B39 * 0.5) > 5:
                                result = 5
                            else:
                                result = 2 + B39 * 0.5
                    else:
                        if B38 == "w":
                            if B39 == 0:
                                result = 1.5
                            else:
                                if (2 + B39 * 0.5) > 5:
                                    result = 5
                                else:
                                    result = 2 + B39 * 0.5
            rec.part_igr = result

    @api.depends ('family_ids')
    def _compute_children(self):
        """
        Fonction permettant le calcul du nombre d'enfants
        """
        children_in_charge = 0
        for emp in self:
            if emp.family_ids:
                for enf in emp.family_ids:
                    if enf.type_parent == 'child':
                        children_in_charge += 1
                        emp.child_in_charge = children_in_charge
                        emp.total_children = children_in_charge

    @api.depends ('birthday')
    def _get_age_employee(self):
        """
        Fonction permettant de calculer l'age de l'employé
        """
        this_date = fields.Datetime.now ()
        for emp in self:
            date_naissance = fields.Datetime.from_string (emp.birthday)
            tmp = relativedelta (this_date, date_naissance)
            emp.age = tmp.years

    @api.depends ('start_date', 'end_date')
    def _get_seniority(self):
        """
        Fonction permettant de definir l'ancienneté
        """
        today = fields.Datetime.now ()

        for emp in self:
            start_date = fields.Datetime.from_string (emp.start_date)
            if emp.end_date:
                end_date = fields.Datetime.from_string (emp.end_date)
                this_date = min (today, end_date)
            else:
                this_date = today
            tmp = relativedelta (this_date, start_date)
            emp.seniority_employee = tmp.years

    def _get_nb_part_cmu(self):
        for emp in self:
            nb = emp.total_children + 1
            if emp.marital == "married":
                nb += 1
            emp.part_cmu = nb

    @api.depends ('type_employee')
    def check_responsible(self):
        for emp in self:
            if emp.type_employee and emp.type_employee != 'employee':
                emp.manager = True
            else:
                emp.manager = False

    def name_get(self):
        result = []
        for emp in self:
            if emp.first_name:
                name = emp.name + ' ' + emp.first_name
            else:
                name = emp.name
            result.append ((emp.id, name))
        return result

    def determine_date_retirement_all_employee(self):
        all_employee = self.env['hr.employee'].search ([])
        self.determine_date_retirement (all_employee)

    def determine_date_retirement(self, employees):
        if employees:
            for rec in employees:
                if rec.company_id and rec.birthday:
                    date_retirement = rec.birthday + relativedelta.relativedelta (
                        years=rec.company_id.retirement_age)
                    first_date = str (fields.Date.from_string (date_retirement) + relativedelta.relativedelta (
                        months=- rec.company_id.first_alert_retraite))
                    second_date = str (fields.Date.from_string (date_retirement) + relativedelta.relativedelta (
                        months=- rec.company_id.second_alert_retraite))
                    rec.date_first_alerte_retraite = first_date
                    rec.date_second_alerte_retraite = second_date
                    rec.estimated_date_retirement = date_retirement
    #     return True

    def cron_send_mail_retirement(self):
        """
        Fonction permettant d'envoyer des emails de notification concernant les départs à la retraite
        :return:
        """
        today = datetime.today ()
        employees = self.search (['|', ('date_first_alerte_retraite', '=', today),
                                  ('date_second_alerte_retraite', '=', today)])
        if employees:
            email_template_id = self.env.ref ('hr_employee_custom.template_alert_email__retirement').id
            email_template = self.env['mail.template'].browse (email_template_id)
            for employee in employees:
                email_template.send_mail (employee.id, force_send=True)

    @api.constrains ('start_date')
    def _check_date_anciennete(self):
        for record in self:
            if record.start_date:
                if record.start_date > fields.Date.today ():
                    raise ValidationError ("La date d'ancienneté doit être inférieure à la date d'aujourd'hui")


    @api.onchange ('birthday')
    def change_birthday(self):
        if self.birthday and self.birthday > date.today ():
            raise ValidationError ("La date d'anniversaire doit être inférieure à la date d'aujourd'hui")

    # les champs en rapport avec l'employé lui-meme
    first_name = fields.Char ("Prénoms", required=True)
    identification_id = fields.Char ("Matricule employé", required=True)
    identification_cnps = fields.Char ('N° CNPS', size=64)
    type = fields.Selection (Type_employee, 'Type', default=False)
    age = fields.Integer ('Âge employé', compute='_get_age_employee')
    phone = fields.Char ("Tél Portable personnel")
    gender = fields.Selection ([('male', 'M'), ('female', 'F'), ('other', 'Autre')], groups="hr.group_hr_user",
                               default="male")
    bank_ids = fields.One2many ("res.partner.bank", "employee_id", "Comptes bancaires", store=True)
    main_bank_id = fields.Many2one("res.partner.bank", "Compte bancaire principale",
                                   domain="[('employee_id', '=', id)]")
    emergency_contact = fields.Char(string="Contact d'urgence" )
    emergency_phone = fields.Char(string="Téléphone d'urgence")
    birthday = fields.Date("")
    place_of_birth = fields.Char("")
    # champs en rapport avec les enfants
    child_in_charge = fields.Integer ("Nombre d'enfants à charge", default=0, compute='_compute_children', store=True)
    total_children = fields.Integer ('Nombre enfant total', compute='_compute_children')
    # champs en rapport avec la RH
    end_date = fields.Date ("Date de départ")
    start_date = fields.Date ("Date de début", required=True)
    date_entree = fields.Date ("Date d'entrée")
    date_anciennete = fields.Date ("Date d'ancienneté")
    category_contract_id = fields.Many2one ('hr.category.contract', 'Catégorie',readonly=True)
    seniority_employee = fields.Integer ("Anciennété", compute="_get_seniority", store=True)
    nature_employe = fields.Selection ([('local', 'Local'), ('expat', 'Expatrié')], "Nature de l'employé",
                                       default='local')
    type_employee = fields.Selection ([('dg', 'DG'),('dga', 'DGA'),('conseiller', 'Conseiller'),('director', 'Directeur'), ('department_chief', 'Chef de departement'),
                                       ('service_chief', 'Chef de service'),('office_chief', 'Chef de bureau'),('unit_chief', "Chef d'unité"), ('employee', 'Collaborateur')],
                                      "Lien hiérarchique")
    # les champs en rapport avec la retraite
    date_first_alerte_retraite = fields.Date ("Date première alerte retraite")
    date_second_alerte_retraite = fields.Date ("Date seconde alerte retraite")
    estimated_date_retirement = fields.Date ("Date prévisionnelle départ retraite")
    # les champs en rapport avec le conjoint l'employé
    conjoint_name = fields.Char (string="Nom conjoint(e)", groups="hr.group_hr_user")
    conjoint_first_name = fields.Char (string="Prénoms conjoint(e)", groups="hr.group_hr_user")
    conjoint_birthdate = fields.Date (string="Date de naissance du conjoint", groups="hr.group_hr_user")
    num_cmu_conjoint = fields.Char ('N° CMU conjoint')
    conjoint_complete_name = fields.Integer ("Nom complet conjoint (e)", groups="hr.group_hr_user")
    gender_conjoint = fields.Selection ([('male', 'M'), ('female', 'F')], "Sexe", groups="hr.group_hr_user")
    # champs en rapport avec la hierachie
    direction_id = fields.Many2one ('hr.department', 'Direction', required=False, domain="[('type', '=', 'direction')]")
    department_id = fields.Many2one ('hr.department', 'Departement', required=False,
                                     domain="[('type', '=', 'department')]")
    service_id = fields.Many2one ('hr.department', 'Service',domain="[('type', '=', 'service')]")
    coach_id = fields.Many2one ('hr.employee', 'Mentor', required=False)
    manager = fields.Boolean (compute='check_responsible', store=True, readonly=False)
    college = fields.Selection ([('cadre', 'Cadre'), ('non_cadre', 'Non cadre')], string="Collège", default=False)
    responsable_payroll_id = fields.Many2one ('hr.employee', 'Gestionnaire de Paie', required=False)
    # champs en rapport avec la citoyenneté de l'employé
    num_cgare = fields.Char ("N° CGRAE")
    num_crrae = fields.Char ('N° CRRAE')
    num_cmu = fields.Char ('N° CMU')
    part_cmu = fields.Integer ("Nombre de part CMU", compute="_get_nb_part_cmu")
    part_igr = fields.Float (compute=_get_part_igr, string='Part IGR')
    # champ en rapport avec les parents
    family_ids = fields.One2many ('hr.parent', 'employee_id', 'Parents/Enfants')
    # champs en rapport avec la visite medicale
    medic_exam_yearly = fields.Date ("Visite médicale annuelle")
    visit_ids = fields.One2many ('hr.visit.medical', 'employee_id', "Visistes médicales")
    # champ en rapport avec les etudes
    diplome_ids = fields.One2many ('hr.diplomes.employee', 'employee_id', 'Diplôme des employés')
    study_school_id = fields.Many2one('hr.school', string="Ecole")
    study_field_id = fields.Many2one('hr.school.field', string="Niveau d'etude")
    recruitment_degree_id = fields.Many2one ('hr.employee.degree', "Niveau d'étude")
    # champ en rapport avec l'accident de travail
    work_accident_ids = fields.One2many ('hr.work_accident', 'employee_id', 'Accidents de travail')
    # champ en rapport avec les sanctions
    sanction_ids = fields.One2many ('hr.sanctions', 'employee_id', 'Sanctions')
    # champ en rapport avec les missions
    mission_ids = fields.One2many ('hr.mission', 'employee_id', 'Missions')
    motif_depart = fields.Text ('Commentaire de depart')
    motif_fin_contract_id = fields.Many2one ('hr.employee.motif.cloture', "Motif de fin")
    receive_mail_notificatif_id = fields.Many2one ("res.company", "Alerte fin de contrat")
    categorie_salariale_id = fields.Many2one ('hr.categorie.salariale', 'Catégorie salariale')
    contract_id = fields.Many2one ('hr.contract', 'Contrat')

    _sql_constraints = [
        ('ID_uniq', 'unique (identification_id)', "Ce matricule existe déjà !"),
    ]


class HrEmployeePublic (models.Model):
    _inherit = 'hr.employee.public'
    _order = 'identification_id'

    first_name = fields.Char ("Prénoms", required=True)
    identification_id = fields.Char ("Matricule employé", required=True)

