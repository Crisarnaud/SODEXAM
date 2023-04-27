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

class HrSite (models.Model):
    _name = "hr.site"
    _description = "Site"

    code = fields.Char ('Code')
    name = fields.Char ('Site')

    _sql_constraints = [
        ('ID_uniq', 'unique (name)', "Ce site existe déjà !"),
    ]


class HrPlatefome (models.Model):
    _name = "hr.plateforme"
    _description = "Plateforme"

    code = fields.Char ('Code')
    name = fields.Char ('Plateforme')
    description = fields.Char ('Description')

    _sql_constraints = [
        ('ID_uniq', 'unique (name)', "Cette plateforme existe déjà !"),
    ]

    class HrProfession (models.Model):
        _name = "hr.profession"
        _description = "Profession de l'employé"

        code = fields.Char ('Code')
        name = fields.Char ('Libellé')

    _sql_constraints = [
        ('ID_uniq', 'unique (name)', "Cette profession existe déjà !"),
    ]


class HrEmployee (models.Model):
    _inherit = 'hr.employee'
    _order = 'identification_id'

    @api.onchange ('plateforme_id')
    def _onchange_plateforme_id(self):
        for emp in self:
            if emp.plateforme_id:
                emp.work_location = emp.plateforme_id.name

    # champs en rapport avec la hierachie
    bureau_id = fields.Many2one ('hr.department', 'Bureau/Unité', domain="[('type', '=', 'bureau')]")
    plateforme_id = fields.Many2one ('hr.plateforme', 'Plateforme', required=False)
    site_id = fields.Many2one ('hr.site', 'Site', required=False)
    profession_id = fields.Many2one ('hr.profession', 'Profession')
