# -*- coding:utf-8 -*-

import time
from datetime import date
from datetime import datetime, timedelta, date
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from odoo import models, api, fields, _, exceptions

from odoo.exceptions import ValidationError
from odoo import fields, osv, api, models
from odoo import tools
from odoo.tools.translate import _

import logging

_logger = logging.getLogger (__name__)



class ResCompany (models.Model):
    _inherit = 'res.company'

    number_of_days_validates = fields.Integer (string='Nombre de jours de validités reçu', default="15",store=True, help="Nombre de jours pour la validité du recu")
    price_of_customer_nas_gen = fields.Integer (string='Montant a payé pour les patients nas et sodexam pour une consultation généraliste', default="0",store=True, help="Montant pour les consultations généraliste Nas et Sodexam")
    price_of_customer_nas_spe = fields.Integer (string='Montant a payé pour les patients nas et sodexam pour une consultation spécialiste', default="10000",store=True, help="Montant pour les consultations spécifiques Nas et Sodexam")
    price_of_insurance_gen = fields.Integer (string="Montant a payé par l'assurance nas et sodexam pour une consultation généraliste", default="2000",store=True)
    price_of_insurance_spe = fields.Integer (string="Montant a payé par l'assurance nas et sodexam pour une consultation spécialiste", default="12000",store=True)