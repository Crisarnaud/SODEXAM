# -*- coding: utf-8 -*-

from odoo import api, fields, osv, exceptions, models


class HeureSupplementaire(models.Model):
    _name = 'hr.attendance.heure.supp'
    _description = "Heure supplementaire"

    name = fields.Char(compute='displayed_name', store=True)
    h_date = fields.Date("Date")
    nb_heure = fields.Float("Nombre d'heure")
    description = fields.Text("Description")
    employee_id = fields.Many2one('hr.employee', 'Employé', ondelete='cascade')
    heure_supp_type_id = fields.Many2one('hr.attendance.heure.supp.type', 'Type', ondelete='cascade')

    state = fields.Selection([('draft', 'Brouillon'), ('confirmed', 'Confirmé'), ('cancel', 'Annulé')], 'Status',
                             default='draft')

    @api.depends('h_date')
    def displayed_name(self):
        self.name = u'Heures Supplémentaires de ' + (self.employee_id.name) + ' du ' + (self.h_date)

    def action_validate(self):
        self.state = 'confirmed'

    def action_draft(self):
        self.state = 'draft'

    def action_refuse(self):
        self.state = 'cancel'

    def action_cancel(self):
        self.state = 'cancel'

    def unlink(self):
        """
           Contrôl à la suppression d'une expression de besoin
            """
        for request in self:
            if request.state != 'draft':
                raise exceptions.ValidationError(
                    str("Vous ne pouvez pas supprimer ce ddcument, veuillez le mettre d'abord en brouillon"))
        return super(HeureSupplementaire, self).unlink()


class TypeHeureSupp(models.Model):
    _name = 'hr.attendance.heure.supp.type'
    _description = "Type heure supplementaire"

    name = fields.Char("Type")
    code = fields.Char("Code", size=128)
    description = fields.Text("Description", )
    active = fields.Boolean('Actif', default=True)

    _sql_constraints = [('code_unique', 'unique(code)', 'Le code doit être unique.')]
