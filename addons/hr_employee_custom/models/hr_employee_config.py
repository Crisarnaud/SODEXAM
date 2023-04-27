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
from odoo import fields, models, api, _
import logging

from odoo.addons.hr_employee_custom.models import hr_employee

_logger = logging.getLogger(__name__)

Type_employee = [('h', 'Horaire'), ('j', 'Journalier'), ('m', 'Mensuel')]


class hr_employee_degree(models.Model):
    _name = "hr.employee.degree"
    _description = "Degree of employee"

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of degrees.",
                              default=1)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name of the Degree of employee must be unique!')
    ]


class domaine(models.Model):
    _name = "hr.diplomes.domaine"
    _description = "Domaine de diplome employe"
    _rec_name = 'libelle'

    libelle = fields.Char('Libellé Domaine', size=64, required=True, readonly=False)


class diplome_employe(models.Model):
    _name = "hr.diplomes.employee"
    _description = "Diplome employe"

    name = fields.Char('Name', size=64, required=False, readonly=False, translate=True)
    diplome_id = fields.Many2one('hr.employee.degree', 'Niveau', required=True)
    domaine_id = fields.Many2one('hr.diplomes.domaine', 'Domaines', required=False, readonly=False)
    reference = fields.Char('Reférence', size=64, required=False, readonly=False)
    date_obtention = fields.Date("Date d'obtention")
    date_start = fields.Date("Date début")
    date_end = fields.Date("Date fin")
    type = fields.Selection([('diplome', 'Diplôme'), ('certif', 'Certification')], "Type", index=True)
    image = fields.Binary('Image')
    employee_id = fields.Many2one('hr.employee', 'Employé')


class HrEmployeeDocument(models.Model):
    _name = "hr.employee.document"
    _inherit = 'mail.thread', 'mail.activity.mixin'
    _description = "Documents de l'employé"

    def _get_employee_id(self):
        return self.env.context.get('active_id')

    name = fields.Char('Libellé document', size=64, required=True, readonly=False)
    reference = fields.Char('Référence', size=64, readonly=False)
    date_start = fields.Date('Début validité')
    date_end = fields.Date('Fin validité')
    type_paper = fields.Many2one('hr.employee.type.document', "Type document")
    employee_id = fields.Many2one('hr.employee', 'Employé', required=False, readonly=True, default=_get_employee_id)


class HrEmployeeTypeDocument(models.Model):
    _name = "hr.employee.type.document"
    _description = "Type Document"

    code = fields.Char('Code', size=64)
    name = fields.Char('Libellé', size=64, required=True, readonly=False)


class HrParents(models.Model):
    _name = "hr.parent"
    _description = "parents de l'employé"

    @api.model
    def send_notifcation_certification(self):
        today = fields.Date.from_string(fields.Date.today())

        enfants = self.search([[('type_parent', '=', 'child')]])

        for eft in enfants:
            if eft.age >= 21:
                # TODO: send notification
                return True
            values = {}

    def _get_employee_id(self):
        return self.env.context.get('active_id')

    @api.depends('date_naissance')
    def _get_age_parent(self):
        this_date = fields.Datetime.now()
        for emp in self:
            date_naissance = fields.Datetime.from_string(emp.date_naissance)
            tmp = relativedelta(this_date, date_naissance)
            emp.age = tmp.years



    # @api.onchange('person_contacted')
    # def _onchange_person_contacted(self):
    #     for emp in self:
    #         if emp.person_contacted:
    #             emp.employee_id.emergency_contact = emp.name
    #
    # @api.onchange('num_contacted')
    # def _onchange_num_contacted(self):
    #     for emp in self:
    #         if emp.num_contacted:
    #             emp.employee_id.emergency_phone = emp.num_contacted

    name = fields.Char('Nom', size=128, required=True, readonly=False)
    first_name = fields.Char("Prénoms", size=225, required=True, readonly=False)
    date_naissance = fields.Date("Date de naissance")
    mobile = fields.Char('Portable', size=128, required=False, readonly=False)
    email = fields.Char('email', size=128, required=False, readonly=False)
    num_cmu = fields.Char("N° CMU", required=False)
    employee_id = fields.Many2one('hr.employee', 'Employé', required=False, readonly=True, default=_get_employee_id)
    age = fields.Integer('Âge', compute='_get_age_parent')
    gender = fields.Selection([('male', 'M'), ('female', 'F')], "Sexe")
    Lien = fields.Selection([('grand_parent', 'Grand père/Grande mère'), ('parent', 'Père / Mère'),
                             ('conjoint', 'Conjoint(e)'), ('enfant', 'Enfant'), ('frere', 'Frère / Soeur'),
                             ('voisin', 'Voisin'),
                             ('oncle', 'Oncle/Tante'), ('cousin', 'Cousin / Cousine'), ('other', 'Autres')],
                            'Lien de parenté', readonly=False)
    type_parent = fields.Selection([('child', 'Enfant'), ('father', 'Père'), ('mother', 'Mère'), ('brother', 'Frère'), ('sister', 'Soeur'), ('aunt', 'Tante'),('cousin', 'Cousin'),('cousine', 'Cousine')], "Type", index=True)
    # person_contacted = fields.Boolean("Personne à contacter", default=False, store=True)
    # num_contacted = fields.Char("Numéro à contacter", store=True)
    certification_frequentation = fields.Boolean("Certificat de frequentation")


class VisiteMedical(models.Model):
    _name = "hr.visit.medical"
    _description = "Gestion des visites medicals"

    name = fields.Char('Libellé', required=True)
    date_prevue = fields.Date("Date prévue", required=True)
    date_effective = fields.Date("Date effective", required=False)
    description = fields.Text("Commentaire")
    lieu_visite = fields.Char("Lieu de la visite", required=True)
    employee_id = fields.Many2one('hr.employee', "Employé", required=False)


class HrDepartement(models.Model):
    _inherit = "hr.department"
    _rec_name = 'name'

    def get_default_type(self):
        return self._context.get('default_type') or False

    name = fields.Char(string='Libellé')
    description = fields.Char('Description')
    type = fields.Selection(
        [('direction', 'Direction'), ('department', 'Département'), ('service', 'Service'), ('bureau', 'Bureau/unité')],
        string="Type", default=get_default_type)


class HrEmployeeMotifCloture(models.Model):
    _name = 'hr.employee.motif.cloture'
    _description = "Motif de cloture"

    name = fields.Char('Libellé', required=True)
    code = fields.Char("Code", size=4)
    description = fields.Text('Description', required=False)


class HrSanction(models.Model):
    _name = 'hr.sanctions'
    _description = "Sanctions"
    name = fields.Char('Motif')
    description = fields.Char(string='Description')
    date_sanction = fields.Date('Date')
    nbre_jour_a_deduire = fields.Integer('Nbre jour à déduire')
    type_sanction_id = fields.Many2one('hr.type_sanctions', 'Type sanction')
    employee_id = fields.Many2one('hr.employee', 'Employe')


class HrTypeSanction(models.Model):
    _name = 'hr.type_sanctions'
    _description = "Type de sanction"

    name = fields.Char('Libelle')


class ResAbatement(models.Model):
    _name = 'res.abatement'
    _description = "Gestion des abatements"

    name = fields.Char("Libellé", required=True, size=255)
    taux = fields.Float("Taux", required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')


class ResCompany(models.Model):
    _inherit = 'res.company'

    abatement_ids = fields.Many2many('res.abatement', 'abament_company_reel', 'company_id', 'abatement_id',
                                     'Abatements')
    num_cnps = fields.Char("Numéro CNPS", size=124)
    num_contribuable = fields.Char("Numéro Contribuable", size=128)
    taux_accident_travail = fields.Float('Taux accident de travail')
    taux_cnps_employee_local = fields.Float('Taux CNPS employé local')
    taux_cnps_employe_expat = fields.Float('aux CNPS employé expatrié')
    taux_cnps_employer = fields.Float('Taux CNPS employeur')
    taux_prestation_familiale = fields.Float('Taux prestation familiale')
    taux_assurance_mater = fields.Float('Taux assurance maternité')
    taux_its = fields.Float('ITS (Taux)')
    taux_fdfp = fields.Float('Taux FDFP')
    taux_fdfp_fc = fields.Float('Taux FDFP FC')
    impot_service = fields.Char("Service d'assiette", required=False)
    max_age_child = fields.Integer('Aĝe maximal enfant à charge', default=21)
    max_assiette_cnps = fields.Float("Plafond regime de retraite mensuel", default=1647315)
    max_assiette_autre_contribution = fields.Float("Plafond regime autres contributions", default=70000)
    mobile = fields.Char("Téléphone cellulaire")
    parcelle = fields.Char("Parcelle")
    general_manager_id = fields.Many2one('hr.employee', 'Directeur Général', required=False)
    direction_general_note = fields.Text("Mot de la direction général", required=False)
    hr_manager_id = fields.Many2one('hr.employee', 'Directeur des Ressources Humaines', required=True)
    first_alert_retraite = fields.Integer(string="Première alerte depart retraite (Mois)", readonly=False)
    second_alert_retraite = fields.Integer(string="Deuxième alerte depart retraite (Mois)", readonly=False)
    signature_drh = fields.Binary("Signature du DRH", required=False)
    alert_receiver_one = fields.Many2one("hr.employee", "Responsable personnel")
    alert_receiver_two = fields.Many2one("hr.employee", "Responsable Paie")
    sigle = fields.Char(string="Sigle de la société")
    date_start_work_hour = fields.Char("Heure Début de travail", default='07H30')


class HrWorkAccident(models.Model):
    _name = 'hr.work_accident'
    _description = "Gestion des accidents de travail"

    name = fields.Char('Référence', required=True)
    accident_date = fields.Date("Date", required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee')
    work_accident_description = fields.Text(string='Description')


class HrMission(models.Model):
    _name = "hr.mission"
    _description = "gestion des missions"

    name = fields.Char('Reference')
    objet_mission = fields.Char('Objet de la mission')
    date_depart = fields.Date('Date départ')
    date_retour = fields.Date('Date retour')
    moyen_transport_id = fields.Many2one('hr.moyens_transport', 'Moyen de transport')
    imputation_budgetaire_id = fields.Many2one('hr.department', 'Imputation Budgetaire')
    destination_ids = fields.Many2many('hr.destination', 'mission_destination_rel', 'mission_id', 'destination_id',
                                       'Destinations')
    employee_id = fields.Many2one('hr.employee', 'Employe')


class HrDestination(models.Model):
    _name = "hr.destination"
    _description = "les destinations des missions"

    name = fields.Char('Destination')


class HrMoyensTransport(models.Model):
    _name = "hr.moyens_transport"
    _description = "Moyens de transport"

    name = fields.Char('Moyen de transport', required=True)


class HrSchool(models.Model):
    _name = "hr.school"
    _description = "Ecoles"

    code = fields.Char('Code')
    name = fields.Char('Libellé', required=True)


class HrSchoolField(models.Model):
    _name = "hr.school.field"
    _description = "Niveau d'etude"

    code = fields.Char('Code')
    name = fields.Char('Libellé')


class ResBank(models.Model):
    _inherit = "res.bank"

    partner_id = fields.Many2one('res.partner', 'Account Holder', ondelete='cascade', index=True,
                                 domain=['|', ('is_company', '=', True), ('parent_id', '=', False)], required=False)
    acronym = fields.Char('Sigle')
    is_main = fields.Boolean("Est la banque principale pour tous", default=False)
    # account_id = fields.Many2one ("account.account", "Compte comptable associé", required=False)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    employee_id = fields.Many2one("hr.employee", "Titulaire", required=False)
    partner_id = fields.Many2one("res.partner", required=False)
    code_guichet = fields.Char('Code guichet', required=False)
    rib = fields.Char('Clé RIB')

    @api.model
    def create(self, vals):
        new_record = super(ResPartnerBank, self).create(vals)
        main_bank = new_record.bank_id.is_main
        if main_bank:
            new_record.employee_id.main_bank_id = new_record.id
            vals_dispatche_line = {
                'bank_id': new_record.id,
                'type': 'balance',
                'employee_id': new_record.employee_id.id
            }
            self.env['hr.employee.salary.dispatched.line'].create(vals_dispatche_line)
        return new_record


class HrSite(models.Model):
    _name = "hr.site"
    _description = "Site"

    code = fields.Char('Code')
    name = fields.Char('Site')

    _sql_constraints = [
        ('ID_uniq', 'unique (name)', "Ce site existe déjà !"),
    ]


class HrPlatefome(models.Model):
    _name = "hr.plateforme"
    _description = "Plateforme"

    code = fields.Char('Code')
    name = fields.Char('Plateforme')
    description = fields.Char('Description')

    _sql_constraints = [
        ('ID_uniq', 'unique (name)', "Cette plateforme existe déjà !"),
    ]


class HrProfession(models.Model):
    _name = "hr.profession"
    _description = "Profession de l'employé"

    code = fields.Char('Code')
    name = fields.Char('Libellé')

    _sql_constraints = [
        ('ID_uniq', 'unique (name)', "Cette profession existe déjà !"),
    ]
