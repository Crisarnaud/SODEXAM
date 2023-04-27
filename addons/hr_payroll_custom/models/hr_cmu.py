# -*- coding:utf-8 -*-


from odoo import api, fields, models, _


class HrCGRAE(models.Model):
    _name = "hr.cmu_rapport"
    _description = "Gestion des rapports CMU"

    def compute(self):
        data = []
        self.env.cr.execute(
            "SELECT employee_id FROM hr_payslip WHERE date_from >= %s AND date_to <= %s AND company_id = %s",
            (self.date_from, self.date_to, self.company_id.id))
        results = self.env.cr.fetchall()
        if results:
            employee_ids = [x[0] for x in results]
            if employee_ids:
                employees = self.env['hr.employee'].search([('type', '!=', 'p'), ('id', 'in', employee_ids)
                                                            ], order='identification_id')
                for emp in employees:
                    val = {
                        'num_cnps': emp.identification_cnps,
                        'num_cmu': emp.num_cmu,
                        'type': 't',
                        'name': emp.name,
                        'first_name': emp.first_name,
                        'birthday': emp.birthday,
                        'gender': emp.gender,
                        'num_cmu_beneficiary': emp.num_cmu,
                        'name_beneficiary': emp.name,
                        'first_name_beneficiary': emp.first_name,
                        'birthday_beneficiary': emp.birthday,
                    }
                    data.append(val)
                    if emp.marital == 'married':
                        val = {
                            'num_cnps': emp.identification_cnps,
                            'num_cmu': emp.num_cmu,
                            'type': 'c',
                            'name': emp.name,
                            'first_name': emp.first_name,
                            'birthday': emp.birthday,
                            'gender': emp.gender_conjoint,
                            'num_cmu_beneficiary': emp.num_cmu,
                            'name_beneficiary': emp.conjoint_name,
                            'first_name_beneficiary': emp.conjoint_first_name,
                            'birthday_beneficiary': emp.conjoint_birthdate,

                        }
                        data.append(val)
                    enfants = self.env['hr.parent'].search(
                        [('employee_id', '=', emp.id), ('type_parent', '=', 'child')])
                    if enfants:
                        for enf in enfants:
                            val = {
                                'num_cnps': emp.identification_cnps,
                                'num_cmu': emp.num_cmu,
                                'type': 'e',
                                'name': emp.name,
                                'first_name': emp.first_name,
                                'birthday': emp.birthday,
                                'gender': enf.gender,
                                'num_cmu_beneficiary': emp.num_cmu,
                                'name_beneficiary': enf.name,
                                'first_name_beneficiary': enf.first_name,
                                'birthday_beneficiary': enf.date_naissance,

                            }
                            data.append(val)
        if data:
            self.line_ids.unlink()
            self.line_ids = self.line_ids.create(data)
        return data

    name = fields.Char('Libellé')
    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    company_id = fields.Many2one('res.company', 'Compagnie', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    line_ids = fields.One2many("hr.cmu_line", "cmu_id", "Lignes")

    def export_xls(self):
        context = self._context
        self.ensure_one()
        datas = {'ids': self.ids}
        datas['model'] = 'hr.cmu'
        return self.env.ref('hr_payroll_custom.report_hr_cmu').with_context(data=datas).report_action(self, data=datas,
                                                                                                      config=False)


class HrCGRAELine(models.Model):
    _name = "hr.cmu_line"
    _description = "Ligne CMU management"

    num_cnps = fields.Char("Numéro CNPS")
    num_cmu = fields.Char("N° CMU assuré")
    type = fields.Selection([('t', 'T'), ('c', 'C'), ('e', 'E')], "Type bénéficiaire")
    name = fields.Char("Nom assuré")
    first_name = fields.Char("Prénoms assuré")
    birthday = fields.Date("Date de naissance assuré")
    gender = fields.Selection([('male', 'H'), ('female', 'F')], "Genre du bénéficiaire")
    cmu_id = fields.Many2one("hr.cmu_rapport", "CMU", required=False)
    num_cmu_beneficiary = fields.Char("N° CMU Beneficiaire")
    name_beneficiary = fields.Char("Nom beneficiaire")
    first_name_beneficiary = fields.Char('Prenoms beneficiaire')
    birthday_beneficiary = fields.Date('Date de naissance beneficiaire')
