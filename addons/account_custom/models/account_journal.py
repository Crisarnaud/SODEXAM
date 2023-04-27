from odoo import fields, models, api, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def _domain_res_users(self):
        return [('groups_id', '=', self.env.ref('account.group_account_user').id)]

    user_access_ids = fields.Many2many('res.users', domain=_domain_res_users)


class AccountMove(models.Model):
    _inherit = 'account.move'


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"