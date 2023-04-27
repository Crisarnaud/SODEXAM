# -*- coding:utf-8 -*-


from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    number_holidays_locaux = fields.Float('Employés locaux', related='company_id.number_holidays_locaux',
                                          readonly=False)
    number_holidays_expat = fields.Float('Employés expatriés', related='company_id.number_holidays_expat',
                                         readonly=False)
    days_before_holidays = fields.Integer(string="Alerte depart congés (Jours)", readonly=False,
                                          related="company_id.days_before_holidays")
    days_after_holidays = fields.Integer(string="Alerte retour congés (Jours)", readonly=False,
                                         related="company_id.days_after_holidays")
    first_alert_real_planning = fields.Integer(string="Première alerte planning réel (Jours)", readonly=False,
                                               related="company_id.first_alert_real_planning",
                                               help="Définir le nombre de jours avant la date de début du planning " \
                                                    "réel des employés pour la première alerte")
    second_alert_real_planning = fields.Integer(string="Deuxième alerte planning réel (Jours)", readonly=False,
                                                related="company_id.second_alert_real_planning",
                                                help="Définir le nombre de jours avant la date de début du planning " \
                                                     "réel des employés pour la deuxième alerte")
    module_hr_holidays_auto = fields.Boolean("Module holidays auto")
