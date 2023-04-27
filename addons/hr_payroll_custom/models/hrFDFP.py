# -*- coding:utf-8 -*-

from odoo import api, fields, models, _


class HrFDFP(models.Model):
    _name = 'hr.fdfp'
    _description = "hr.fdfp"

    name = fields.Char('Nom', required=True, size=155)
    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    company_id = fields.Many2one('res.company', 'Compagnie', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    type_employe = fields.Selection([('m', 'Mensuel'), ('j', 'Journalier'), ('h', 'Horaire'),
                                     ('all', 'Tous les employés')], "Livre de paie pour ", default="all")
    line_ids = fields.One2many('hr.fdfp.line', 'fdfp_id', "lignes")
    salaries_number = fields.Integer("Effectif des salariés")
    amount_total_contributed = fields.Float("Montant total à payer", digits=(12, 0))

    def compute(self):
        self.line_ids.unlink()
        slip_obj = self.env['hr.payslip']
        all_slips = slip_obj.search([('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to),
                                     ('company_id', '=', self.company_id.id)])
        lines = []
        amount = 0
        if all_slips:
            if self.type_employe != 'all':
                all_slips = all_slips.filtered(lambda slip: slip == self.type_employe)
            self.env.cr.execute("SELECT COUNT(DISTINCT(employee_id)) FROM hr_payslip WHERE id=ANY(%s)",
                                (all_slips.ids,))
            result = self.env.cr.dictfetchone()
            if result:
                self.salaries_number = result['count']
            fdfp_config = self.env['hr.fdfp.config'].search([])
            if fdfp_config:
                for fdfp in fdfp_config:
                    self.env.cr.execute("SELECT salary_rule_id as salary_rule,sum(amount) as amount, sum(total) as total"
                                        " FROM hr_payslip_line WHERE salary_rule_id = %s AND slip_id=ANY(%s) GROUP BY "
                                        "salary_rule_id",(fdfp.rule_id.id, all_slips.ids,))
                    results = self.env.cr.dictfetchone()
                    if results:
                        vals = {
                            'rule_id': fdfp.rule_id.id,
                            'taux': fdfp.taux,
                            'brut_total': results['amount'],
                            'amount_contributed': results['amount'] * fdfp.taux /100
                        }
                        amount += vals['amount_contributed']
                        lines.append(vals)

        self.line_ids = lines
        self.amount_total_contributed = amount


class HrFDFPLine(models.Model):
    _name = 'hr.fdfp.line'
    _description = "hr.fdfp.line"

    rule_id = fields.Many2one('hr.salary.rule', "Règle salariale", required=True)
    brut_total = fields.Float("Remunerations brutes totales", digits=(12,0))
    taux = fields.Float("Taux", digits=(12,2))
    amount_contributed = fields.Float("Montant mensuel", digits=(12,0))
    fdfp_id = fields.Many2one("hr.fdfp", "Déclaration FDFP", required=False)


