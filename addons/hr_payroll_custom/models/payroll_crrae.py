from odoo import fields, models, api


class PayrollCrrae(models.Model):
    _name = 'hr_crrae.payroll_crrae'
    _description = 'CRRAE'

    name = fields.Char('Libellé')
    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    periode = fields.Char("Période")
    periode_regul = fields.Char("Période à régulariser")
    assiette = fields.Char("Assiette")
    motif_changement = fields.Char("Motif de changement")
    payroll_crrae_line_ids = fields.One2many('hr_crrae.payroll_crrae_line', 'payroll_crrae_id', 'Ligne CRRAE')
    company_id = fields.Many2one('res.company', 'Compagnie', default=lambda self: self.env.user.company_id.id,
                                 required=True)

    def compute_data(self):
        _query = """
            SELECT DISTINCT
                e.id as employee_id,                
                plce.total as crrae_employee,
                plcp.total as crrae_employer,
                plfe.total as faam_employee,
                plfp.total as faam_employer
            FROM 
                (SELECT * FROM hr_payslip WHERE employee_id IN (SELECT id FROM hr_employee where is_crrae_contributor = True) AND
                date_from >= %(date_from)s AND date_to <= %(date_to)s AND company_id = %(company_id)s) p
                INNER JOIN hr_employee e on (e.id = p.employee_id)
                INNER JOIN hr_payslip_line plce on (e.id = plce.employee_id and plce.code = 'CRRAE_E')
                INNER JOIN hr_payslip_line plcp on (e.id = plcp.employee_id and plcp.code = 'CRRAE_PART')
                INNER JOIN hr_payslip_line plfe on (e.id = plfe.employee_id and plfe.code = 'C_FAAM_E')
                INNER JOIN hr_payslip_line plfp on (e.id = plfp.employee_id and plfp.code = 'CRRAE_FAAM_P')
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
        datas = {'ids': self.ids, 'model': self._name}
        self.payroll_crrae_line_ids.unlink()
        self.payroll_crrae_line_ids = results


class PayrollCrraeLine(models.Model):
    _name = 'hr_crrae.payroll_crrae_line'
    _description = "Ligne de CRRAE"

    name = fields.Char('Matricule', related="employee_id.identification_id", strore=True)
    crrae_employee = fields.Integer('CRRAE Employé')
    faam_employee = fields.Integer('CRRAE FAAM Employé')
    crrae_employer = fields.Integer('CRRAE Employeur')
    faam_employer = fields.Integer('CRRAE FAAM Employeur')
    employee_id = fields.Many2one('hr.employee', 'Employé')
    payroll_crrae_id = fields.Many2one('hr_crrae.payroll_crrae', 'CRRAE')
