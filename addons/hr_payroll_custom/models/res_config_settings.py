# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_hr_cnps_mensuel = fields.Boolean(string='CNPS Mensuelle')
    module_hr_cnps_trimestriel = fields.Boolean(string='CNPS Trimestrielle')
    alert_send_payslip = fields.Integer(string="Alerte d'envoi de fiche de paie par mail (en jours)'",
                                        store=True, help="Définir le jour d'envoi de fiche de paie par mail")