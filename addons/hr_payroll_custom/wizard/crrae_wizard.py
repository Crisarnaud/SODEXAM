# -*- coding:utf-8 -*-


from odoo import api, fields, models, _


class HrCCRAE(models.TransientModel):
    _name = "hr.crrae"
    _description = "Gestion des rapports CRRAE"

    name = fields.Char('Libellé')
    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    periode = fields.Char("Période")
    periode_regul = fields.Char("Période à régulariser")
    assiette = fields.Char("Assiette")
    motif_changement = fields.Char("Motif de cganement")
    company_id = fields.Many2one('res.company', 'Compagnie', required=True, default=lambda self: self.env.user.company_id.id)

    def compute_data(self):
        _query = """
            SELECT
                e.id as employee_id,
                e.identification_id as matricule,
                e.num_crrae as num_crrae,
                e.name as name,
                e.first_name as prenoms,
                plce.total as crrae_employee,
                plcp.total as crrae_employer,
                plfe.total as faam_employee,
                plfp.total as faam_employer
            FROM 
                (SELECT * FROM hr_payslip WHERE employee_id IN (SELECT id FROM hr_employee) AND
                date_from >= %(date_from)s AND date_to <= %(date_to)s AND company_id = %(company_id)s) p
                LEFT JOIN hr_employee e on (e.id = p.employee_id)
                LEFT JOIN hr_payslip_line plce on (e.id = plce.employee_id and plce.code = 'CRRAE_E')
                LEFT JOIN hr_payslip_line plcp on (e.id = plcp.employee_id and plcp.code = 'CRRAE_PART')
                LEFT JOIN hr_payslip_line plfe on (e.id = plfe.employee_id and plfe.code = 'C_FAAM_E')
                LEFT JOIN hr_payslip_line plfp on (e.id = plfp.employee_id and plfp.code = 'CRRAE_FAAM_P')
            GROUP BY
                e.id,
                plce.total,
                plcp.total,
                plfe.total,
                plfp.total
        """

        _params = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_id': self.company_id.id,
        }

        self.env.cr.execute(_query, _params)
        results = self.env.cr.dictfetchall()
        self.ensure_one()
        datas = {'ids': self.ids}
        datas['model'] = self._name
        return self.env.ref('hr_payroll_custom.report_hr_crrae').with_context(data=results).report_action(self, data=datas,
                                                                                           config=False)