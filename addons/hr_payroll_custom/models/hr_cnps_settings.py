# -*- coding:utf-8 -*-


from odoo import api, fields, _, models

Type_employee = [('j', 'Journalier'), ('m', 'Mensuel')]


class HrCnpsSettings(models.Model):
    _name = "hr.cnps.setting"
    _description = "settings of CNPS"

    name = fields.Char("Libellé", required=True)
    active = fields.Boolean("Actif", default=True)
    sequence = fields.Integer('Sequence', default=10)
    amount_min = fields.Float("Montant Min")
    amount_max = fields.Float('Montant Max')
    type = fields.Selection(Type_employee, 'Type', required=False, default=False)


class HrCnpsCotisationLineTemplate(models.Model):
    _name = "hr.cnps.cotisation.line.template"
    _description = "Ligne du modèle de cotisation CNPS"

    name = fields.Char("Designation", required=True)
    company_id = fields.Many2one("res.company", "Société", required=True,
                                 default=lambda self: self.env.user.company_id.id)
    taux = fields.Float("Taux")
    sequence = fields.Integer("Sequence", default=10)
    active = fields.Boolean("Actif", default=True)
    type = fields.Selection([('cnps', 'Régime de retraite'), ('other', 'Autres régimes')], 'Type')
    account_id = fields.Many2one('account.account', 'Compte comptable associé', required=False,
                                 domain="[('company_id', '=', company_id)]")
