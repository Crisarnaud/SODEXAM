import logging
from datetime import date
from nis import cat

from odoo import api, fields, models

_logger = logging.getLogger (__name__)


class HrReportWizard (models.TransientModel):
    _name = "hr.employee.report.wizard"
    _description = "Assistant etat des employes"

    department_ids = fields.Many2many ('hr.department', string='Département')
    gender = fields.Selection ([('male', 'M'), ('female', 'F')], string='Genre')
    all_gender = fields.Boolean ('Tous les genres')
    all_depts = fields.Boolean ('Tous les départements')
    all_directions = fields.Boolean ('Toutes les directions')
    all_services = fields.Boolean ('Tous les services')
    category_contract_ids = fields.Many2many ('hr.category.contract', string='Catégorie de contrat')
    all_category_contract = fields.Boolean ('Toutes les catégories de contrat')

    def generate_data(self):
        if self.all_depts or not self.department_ids:
            dep = (1, '=', 1)
        else:
            dep_rc = []
            for department in self.department_ids:
                dep_rc.append (department.id)
                if department.type == 'department':
                    dep = ('department_id', 'in', dep_rc)
                if department.type == 'direction':
                    dep = ('direction_id', 'in', dep_rc)
                if department.type == 'service':
                    dep = ('service_id', 'in', dep_rc)

        if self.all_gender or not self.gender:
            gend = (1, '=', 1)
        else:
            gend = ('gender', '=', self.gender)
        if self.all_category_contract or not self.category_contract_ids:
            cat = (1, '=', 1)
        else:
            cat_rc = []
            for cat in self.category_contract_ids:
                cat_rc.append (cat.id)
            cat = ('category_id', 'in', cat_rc)

        employees = self.env['hr.employee'].search ([dep, gend, ('active', '=', True)], order="identification_id asc")

        res = []
        if employees:
            for employee in employees:
                contract = self.env['hr.contract'].search ([('employee_id', '=', employee.id), ('state', '=', 'open'),
                                                            ('active', '=', True), cat], limit=1)
                if self.category_contract_ids and not contract:
                    continue
                gender = ''
                if employee.gender == 'male':
                    gender = 'M'
                elif employee.gender == 'female':
                    gender = 'F'
                val = {
                    'identification_id': employee.identification_id,
                    'name': str (employee.name) + ' ' + str (employee.first_name),
                    'job_id': employee.job_id.name if employee.job_id else '',
                    # 'bureau_id': employee.bureau_id.name if employee.bureau_id else '',
                    'service_id': employee.service_id.name if employee.service_id else '',
                    'direction_id': employee.direction_id.name if employee.direction_id else '',
                    'department_id': employee.department_id.name if employee.department_id else '',
                    'plateforme_id': employee.plateforme_id.name if employee.plateforme_id else '',
                    'gender': gender,
                    # 'college': college,
                    'cat': employee.categorie_salariale_id.name if employee.categorie_salariale_id else '',
                    'college': employee.category_contract_id.name if employee.category_contract_id else '',
                    'type_contrat': contract.contract_type_id.name or '',
                    'age': employee.age,
                    'birthday': employee.birthday.strftime (
                        '%d/%m/%Y') if employee.birthday else '',
                    'start_date': employee.start_date.strftime (
                        '%d/%m/%Y') if employee.start_date else '',
                    'date_start': employee.date_anciennete.strftime (
                        '%d/%m/%Y') if employee.date_anciennete else '',
                }
                res.append (val)
        return res

    def add_hr_manager_signature(self):
        res = []
        emp = self.env['hr.employee'].search ([], limit=1)
        val = {
            'manager': str (emp.company_id.hr_manager_id.first_name) + ' ' + str (emp.company_id.hr_manager_id.name)
        }
        res.append (val)
        return res

    def print_report_xls(self):
        data = {
            'lines': self.generate_data (),
            'ids': self.id,
            'form': self.read (),
            'gender': self.gender
        }
        return self.env.ref ('hr_contract_custom.action_report_employee_xls').report_action (self, data=data)

    def print_report_pdf(self):
        data = {'model': self._name, 'form': self.read (), 'contract_types': self.generate_data (),
                'manager': self.add_hr_manager_signature (), 'gender': self.gender}

        return self.env.ref ('hr_contract_custom.action_report_employee_pdf').report_action (self, data=data)
