from odoo import fields, models, api


class ModelName(models.TransientModel):
    _name = 'hr_payroll_custom.workforce_by_detailed_position'
    _description = 'Effectif par position détaillée'

    job_ids = fields.Many2many('hr.job', 'workforce_by_detailed_position_job_rel', 'job_id',
                               'workforce_by_detailed_position_id', string='Poste(s)')
    company_id = fields.Many2one('res.company', 'Compagnie', required=True, default=1)

    def get_header(self):
        res = []
        head_detail = "EFFECTIF"
        res.append(head_detail)
        return res

    def get_data(self):
        res = []
        job_list = []
        if self.job_ids:
            for job in self.job_ids:
                job_list.append(job.id)
            check_jobs = ('id', 'in', job_list)
        else:
            check_jobs = (1, '=', 1)
        jobs = self.env['hr.job'].search([check_jobs], order="name")
        if jobs:
            for job in jobs:
                res_job = {}
                employees_male = self.env['hr.employee'].search_count([('job_id', '=', job.id),
                                                                       ('gender', '=', 'male')])
                employees_female = self.env['hr.employee'].search_count([('job_id', '=', job.id),
                                                                         ('gender', '=', 'female')])
                res_job['job'] = job.name
                res_job['male'] = employees_male
                res_job['female'] = employees_female
                res.append(res_job)
        return res

    def print_report_xls(self):
        data = {
            'model': self._name,
            'header': self.get_header(),
            'lines': self.get_data()
        }
        return self.env.ref('hr_payroll_custom.action_report_workforce_by_detailed_position_xls').report_action(self,
                                                                                                               data=data)

    def print_report_pdf(self):
        data = {
            'model': self._name,
            'header': self.get_header(),
            'lines': self.get_data()
        }
        return self.env.ref('hr_payroll_custom.action_report_workforce_by_detailed_position_pdf').report_action(self,
                                                                                                            data=data)
