# -*- coding: utf-8 -*-


import time
from odoo import models, fields, api, osv, _
from odoo.exceptions import ValidationError
from datetime import datetime


class Convention (models.Model):
    _name = "hr.convention"
    _description = "Convention"

    name = fields.Char ("Name", size=128, required=True)
    code = fields.Char ("code", size=3)

    description = fields.Text ("Description")
    secteurs_ids = fields.One2many ("hr.secteur.activite", "hr_convention_id", "Secteurs d'activtés")


class HrSecteurActivity (models.Model):
    _name = "hr.secteur.activite"
    _description = "Secteur d'activite"

    name = fields.Char ("Libellé", size=128, required=True)
    description = fields.Text ("Description")
    hr_convention_id = fields.Many2one ("hr.convention", "Convention", required=True)
    salaire_ids = fields.One2many ("hr.categorie.salariale", "hr_secteur_activite_id", "Catégories salariales")


class CategorieSalarial (models.Model):
    _name = "hr.categorie.salariale"
    _description = "Categorie salariale"

    name = fields.Char ('Libellé', size=64, required=False)
    salaire_base = fields.Float ("Salaire de base")
    description = fields.Text ('Description')
    hr_secteur_activite_id = fields.Many2one ('hr.secteur.activite', "Secteur d'activité")


class HrEmployee (models.Model):
    _inherit = "hr.employee"

    payment_method = fields.Selection (
        [('espece', 'Espèces'), ('virement', 'Virement bancaire'), ('cheque', 'Chèques')],
        string='Moyens de paiement', required=False)
    contract_state = fields.Selection (string='Etat Contrat', related='contract_id.state', store=True)

    def getInputsPayroll(self, contract, date_from, date_to):
        res = []
        primes = contract.hr_payroll_prime_ids
        input_basic = self.env['hr.salary.rule'].search ([('code', '=', 'BASIC')], limit=1)
        input_surs = self.env['hr.salary.rule'].search ([('code', '=', 'SURSA')], limit=1)
        res = [
            {
                'name': "Salaire de base",
                'code': "BASE",
                'contract_id': contract.id,
                'amount': contract.wage,
                'salary_rule_id': input_basic.id
            },
            {
                'name': "Sursalaire",
                'code': "SURSA",
                'contract_id': contract.id,
                'amount': contract.sursalaire,
                'salary_rule_id': input_surs.id
            }
        ]
        if contract.employee_id.company_id and contract.employee_id.company_id.bonus_transport > 0:
            bonus_transport = contract.employee_id.company_id.bonus_transport
        else:
            raise ValidationError (_ ("Verifier que le contrat {} est rattaché à un employé et que le montant de la "
                                      "prime de transport est bien définie dans les données de la société."
                                      .format (contract.name)))
        input_trsp = self.env['hr.salary.rule'].search ([('code', '=', 'TRSP')], limit=1)
        input_trsp_imp = self.env['hr.salary.rule'].search ([('code', '=', 'TRSP_IMP')], limit=1)
        for prime in primes:
            # input_s = self.env['hr.salary.rule'].search([('code', '=', prime_id.code)], limit=1)
            if prime.prime_id.code == "TRSP":
                if prime.montant_prime > bonus_transport:
                    montant_imp = prime.montant_prime - bonus_transport
                    inputs = {
                        'name': "Prime de transport imposable",
                        'code': "TRSP_IMP",
                        'contract_id': contract.id,
                        'amount': montant_imp,
                        'salary_rule_id': input_trsp_imp.id
                    }
                    res += [inputs]
                    inputs = {
                        'name': prime.prime_id.name,
                        'code': prime.code,
                        'contract_id': contract.id,
                        'amount': bonus_transport,
                        'salary_rule_id': input_trsp.id
                    }
                    res += [inputs]
                else:
                    inputs = {
                        'name': prime.prime_id.name,
                        'code': prime.code,
                        'contract_id': contract.id,
                        'amount': prime.montant_prime,
                    }
                    res += [inputs]
            else:
                sal_rule_id = self.env['hr.salary.rule'].search([('code', '=', prime.code)], limit=1)
                inputs = {
                    'name': prime.prime_id.name,
                    'code': prime.code,
                    'contract_id': contract.id,
                    'amount': prime.montant_prime,
                    'salary_rule_id': sal_rule_id.id
                }
                res += [inputs]
        return res


class HrPayrollPrime (models.Model):
    _name = "hr.payroll.prime"
    _description = "prime"

    name = fields.Char ('Libellé', size=64, required=True)
    code = fields.Char ('Code', size=64, required=True, store=True)
    description = fields.Text ('Description')


class HrPayrollPrimeAmount (models.Model):
    _name = "hr.payroll.prime.montant"
    _description = "Primes management"

    @api.depends ('prime_id')
    def _get_code_prime(self):
        for rec in self:
            rec.code = rec.prime_id.code

    prime_id = fields.Many2one ('hr.payroll.prime', 'Prime', required=True, store=True)
    code = fields.Char ("Code", compute='_get_code_prime')
    contract_id = fields.Many2one ('hr.contract', 'Contrat')
    montant_prime = fields.Integer ('Montant', required=True)


class res_country (models.Model):
    _inherit = 'res.country'

    nationalite = fields.Char ('Nationalité', size=64, required=False, readonly=False)


class res_city (models.Model):
    _name = "res.ville"
    _description = 'Ville'

    name = fields.Char ('Ville', size=64, required=False, readonly=False)
    country_id = fields.Many2one ('res.country', 'Pays', required=False)


class res_commune (models.Model):
    _name = "res.commune"
    _description = 'Commune'

    name = fields.Char ('Ville', size=64, required=False, readonly=False)
    ville_id = fields.Many2one ('res.ville', 'Ville', required=False),


class res_quartier (models.Model):
    _name = "res.quartier"
    _description = 'Quartier'

    name = fields.Char ('Quartier', size=64, required=False, readonly=False)
    commune_id = fields.Many2one ('res.commune', 'Commune', required=False)


class res_partner (models.Model):
    _inherit = 'res.partner'

    @api.onchange ('ville_id')
    def onchange_ville_id(self):
        if not self.ville_id:
            return {}
        else:
            return {
                'value': {
                    'city': self.ville_id.name
                }
            }

    ville_id = fields.Many2one ('res.ville', 'Ville', required=False)
    commune_id = fields.Many2one ('res.commune', 'Commune', required=False)
    quartier_id = fields.Many2one ('res.quartier', 'Quartier', required=False)
    ilot = fields.Char ('Ilot', size=64, required=False, readonly=False)
    lot = fields.Char ('Lot', size=64, required=False, readonly=False)


class HrCategorieSalaire (models.Model):
    _name = "hr.categorie.salaire"
    _description = "Categorie de salaire"

    name = fields.Char ('Libellé', required=True)
    sequence = fields.Integer ('Séquence', required=True, default=10)
    active = fields.Boolean ('Actif')
    code = fields.Char ('Code', size=2, required=True)
    description = fields.Text ('Description')


class HrCatgeryContract (models.Model):
    _name = "hr.type.contract"
    _description = "Type de contrat"

    name = fields.Char ("Libellé ", required=True)
    code = fields.Char ("Code ")
    delai_notif_fin = fields.Integer ("Fin contrat (jours)")
    delai_notif_essai = fields.Integer ("Fin période d'essai (jours)")
    description = fields.Text ("Description", required=False)


class ResCompany (models.Model):
    _inherit = 'res.company'

    alert_trial_contract_expiry = fields.Integer (string="Alerte de fin de contrat essai (Jours)", default=0)
    alert_contract_expiry_cadre = fields.Integer (string="Alerte de fin de contrat pour les cadres (Jours)",
                                                  default=0)
    alert_contract_expiry_non_cadre = fields.Integer (string="Alerte de fin de contrat pour les non cadres (Jours)",
                                                      default=0)

    first_alert_real_planning = fields.Integer (string="Première alerte planning réel (Jours)", readonly=False)
    second_alert_real_planning = fields.Integer (string="Deuxième alerte planning réel (Jours)", readonly=False)
