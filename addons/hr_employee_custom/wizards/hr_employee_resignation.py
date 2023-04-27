from datetime import date
from odoo import api, fields, models


class HrEmployeeResignation(models.TransientModel):
    _name = "hr_employee_custom.employee_resignation"
    _description = "Demission des employes"

    motif_fin_contrat_ids = fields.Many2many('hr.employee.motif.cloture', 'employee_motif_resignation_rel',
                                             'employee_resignation_id', 'motif_if', 'Motif de départ')
    date_debut = fields.Date('Début')
    date_fin = fields.Date('Fin')
    all_motif = fields.Boolean('Tous les motifs')

    def computeEmployeeResignation(self):
        motif_list = []
        if self.date_debut:
            check_date_start = ('end_date', '>=', self.date_debut)
        else:
            check_date_start = (1, '=', 1)
        if self.date_fin:
            check_date_end = ('end_date', '<=', self.date_fin)
        else:
            check_date_end = (1, '=', 1)

        if self.motif_fin_contrat_ids and not self.all_motif:
            for motif in self.motif_fin_contrat_ids:
                motif_list.append(motif.id)
        else:
            motifs = self.env['hr.employee.motif.cloture'].search([])
            for motif in motifs:
                motif_list.append(motif.id)
        employee_list = self.env['hr.employee'].search([('motif_fin_contract_id', 'in', motif_list),
                                                        check_date_start, check_date_end,
                                                        '|', ('active', '=', True), ('active', '=', False)],
                                                       order="identification_id asc")
        res = []
        if employee_list:
            for emp in employee_list:
                gender = ''
                if emp.gender == 'male':
                    gender = 'M'
                elif emp.gender == 'female':
                    gender = 'F'

                category_contrat_id = ''
                contrat_empl = self.env['hr.contract'].search([('employee_id', '=', emp.id)])

                if contrat_empl:
                    category_contrat_id = emp.category_contract_id.name
                    cat = contrat_empl.categorie_salariale_id.name if contrat_empl.categorie_salariale_id else ''
                else:
                    cat = emp.categorie_salariale_id.name if emp.categorie_salariale_id else ''
                val = {
                    'matricule': emp.identification_id or '',
                    'cat': cat or '',
                    'college': emp.category_contract_id.name or '',
                    'age': emp.age or '',
                    'gender': gender or '',
                    'birthday': emp.birthday.strftime("%d/%m/%Y") if emp.birthday else '',
                    'anciennete': emp.start_date.strftime("%d/%m/%Y") if emp.start_date else '',
                    'start_date': emp.start_date or '',
                    'name': (str(emp.name) + ' ' + str(emp.first_name)) or '',
                    'job_id': emp.job_id.name if emp.job_id else '',
                    'department_id': emp.department_id.description if emp.department_id else '',
                    'service_id': emp.service_id.description if emp.service_id else '',
                    'direction_id': emp.direction_id.description if emp.direction_id else '',
                    'date_embauche': emp.start_date.strftime("%d/%m/%Y") if emp.start_date else '',
                    'date_depart': emp.end_date.strftime("%d/%m/%Y") if emp.end_date else '',
                    'motif_depart': emp.motif_fin_contract_id.name if emp.motif_fin_contract_id else '',
                    'type_contrat': contrat_empl.contract_type_id.name or ''
                }
                res.append(val)
        return res

    def add_hr_manager_signature(self):
        res = []
        emp = self.env['hr.employee'].search([], limit=1)
        val = {
            'manager': str(emp.company_id.hr_manager_id.first_name) + ' ' + str(emp.company_id.hr_manager_id.name)
        }
        res.append(val)
        return res

    def total_employee(self):
        emp = []
        total_employee = self.env['hr.employee'].search([])
        total_male = self.env['hr.employee'].search([('gender', '=', 'male')])
        total_female = self.env['hr.employee'].search([('gender', '=', 'female')])
        val = {
            'total_employee': len(total_employee),
            'total_male': len(total_male),
            'total_female': len(total_female)
        }
        emp.append(val)
        return emp


    def print_employee_resignation_xls(self):
        data = {
            'lines': self.computeEmployeeResignation(),
            'ids': self.id,
            'form': self.read(),
        }
        return self.env.ref('hr_employee_custom.action_employee_resignation').report_action(self, data=data)


    def print_employee_resignation_pdf(self):
        data = {'model': self._name, 'form': self.read(), 'motifs': self.computeEmployeeResignation(),
                'manager': self.add_hr_manager_signature()}
        return self.env.ref('hr_employee_custom.action_employee_resignation_pdf').report_action(self, data=data)
