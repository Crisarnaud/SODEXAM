# -*- coding:utf-8 -*-

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    number_holidays_locaux = fields.Float('Nombre de jours de congés mensuels à attribuer employé nationaux',
                                          default='2.2')
    number_holidays_expat = fields.Float('Nombre de jours de congés mensuels à attribuer employé expatriés',
                                         default='5')
    days_before_holidays = fields.Integer(string="Alerte avant congés (Jours)")
    days_after_holidays = fields.Integer(string="Alerte après congés (Jours)")
    first_alert_real_planning = fields.Integer(string="Première alerte planning réel (Jours)", readonly=False)
    second_alert_real_planning = fields.Integer(string="Deuxième alerte planning réel (Jours)", readonly=False)