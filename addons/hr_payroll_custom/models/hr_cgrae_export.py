# -*- coding:utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrCGRAE(models.Model):
    _name = "hr.cgrae"
    _description = "Gestion des rapports"

    def _get_cumul(self):
        for c in self:
            c.total_base = sum([x.amount_brut for x in c.line_ids])
            c.total_cgrae_employee = sum([x.amount_cgrae_employe for x in c.line_ids])
            c.total_cgrae_employer = sum([x.amount_cgrae_employer for x in c.line_ids])
            c.count_cotisant = len(c.line_ids)

    name = fields.Char('Libellé')
    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    company_id = fields.Many2one('res.company', 'Compagnie', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    count_cotisant = fields.Integer("Nombre de cotisants", compute="_get_cumul")
    total_base = fields.Integer("SOLDE BRUT INDICIAIRE", compute="_get_cumul")
    total_cgrae_employee = fields.Integer("Total part salariale", compute="_get_cumul")
    total_cgrae_employer = fields.Integer("Total part patronale", compute="_get_cumul")
    line_ids = fields.One2many("hr.cgrae.line", 'cgrae_id', "Lignes", required=False)

    def _print_report(self, data):
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('hr_payroll_custom.report_hr_payroll').with_context(landscape=True).report_action(self,
                                                                                                              data=data)

    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.ids
        data['model'] = self._name
        return self.env.ref('hr_payroll_custom.hr_cgrae_list').with_context(landscape=True).report_action(self,
                                                                                                          data=data)

    def compute(self):
        data = []
        query = """
            SELECT 
                p.id,
                e.id as employee_id,
                e.company_id as company_id,
                e.identification_id as matricule,
                ple.total as cgrae_e,
                plp.total as cgrae_p,
                plp.amount as base
            FROM
                (SELECT * FROM hr_payslip WHERE employee_id IN (SELECT id FROM hr_employee WHERE type='p') AND
                date_from >= %(date_from)s AND date_to <= %(date_to)s AND company_id = %(company_id)s) p
                    LEFT JOIN hr_employee e on (e.id = p.employee_id and e.type = 'p')
                    LEFT JOIN hr_payslip_line ple on (ple.slip_id = p.id and  ple.code = 'CGRAE_E')
                    LEFT JOIN hr_payslip_line plp on (plp.slip_id = p.id and plp.code = 'CGRAE_P')
            GROUP BY
                p.id,
                e.id,
                e.identification_id,
                e.company_id,
                ple.total,
                plp.total,
                plp.amount
            ORDER BY
                e.identification_id
        """
        params = {
            'company_id': self.company_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to
        }

        self.env.cr.execute(query, params)
        results = self.env.cr.dictfetchall()
        if results:
            i = 0
            for res in results:
                i += 1
                val = {
                    'num_order': i,
                    'employee_id': res['employee_id'],
                    'amount_cgrae_employe': res['cgrae_e'],
                    'amount_cgrae_employer': res['cgrae_p'],
                    'amount_brut': res['base'],
                    'amount_cotisation_total': res['cgrae_e'] + res['cgrae_p'],
                    'observation': '',
                }
                data.append(val)
        if data:
            self.line_ids.unlink()
            self.line_ids = data
        return


class HrCGRAELine(models.Model):
    _name = "hr.cgrae.line"
    _description = "Ligne de CGRAE"

    num_order = fields.Integer("N°")
    employee_id = fields.Many2one("hr.employee", "Employé", required=True)
    amount_brut = fields.Float("Salaires Bruts Mensuel")
    amount_cgrae_employe = fields.Float("Cotisation Mensuel (8.33%)")
    amount_cgrae_employer = fields.Float("Cotisation Mensuel (16.67%)")
    amount_cotisation_total = fields.Float("Cotisation Total (25%)")
    observation = fields.Text("Observation")
    cgrae_id = fields.Many2one("hr.cgrae", "CGARE", required=False)
