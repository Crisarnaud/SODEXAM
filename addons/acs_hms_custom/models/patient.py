import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _
import logging

_logger = logging.getLogger (__name__)


class HmsPatient (models.Model):
    _inherit = 'hms.patient'
    _description = 'hms.patient'

    @api.depends ('birthday')
    def _get_age_employee(self):
        """
        Fonction permettant de calculer l'age de l'employé
        """
        this_date = fields.Datetime.now ()
        for rec in self:
            rec.age = ''
            date_naissance = fields.Datetime.from_string (rec.birthday)
            tmp = relativedelta (this_date, date_naissance)
            rec.age = str(tmp.years) + ("Ans") + ' ' + str(tmp.months) + ("Mois") + ' ' + str(tmp.days) +("Jours")
            if tmp.years < 1:
                rec.age =str(tmp.months) + ("Mois") + ' ' + str(tmp.days) + ("Jours")

    first_name = fields.Char ("Name")
    last_name = fields.Char ("Last name")
    age = fields.Char ("Age", compute=_get_age_employee)
    code_company = fields.Char ("Code")

    @api.onchange ('birthday')
    def change_birthday(self):
        if self.birthday and self.birthday > date.today ():
            raise ValidationError ("La date de naissance doit être inférieure à la date d'aujourd'hui")

    @api.onchange ('first_name', 'last_name')
    def get_name(self):
        """ Onchange function to combine name and last_name """
        if self.first_name:
            if self.last_name:
                self.last_name = self.last_name.upper ()
                self.name = f"{self.last_name} {self.first_name}"
