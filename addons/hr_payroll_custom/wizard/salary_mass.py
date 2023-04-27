from odoo import fields, models, api


class SalaryMass(models.TransientModel):
    _name = 'hr_payroll_custom.salary_mass'
    _description = 'Masse salariale'

    date_start = fields.Date('Date début', help="Définissez la date de début. Cette date sera comparée à la date "
                                                "d'embauche des agents")
    date_end = fields.Date('Date fin', help="Définissez la date de fin. Cette date sera comparée à la date d'embauche "
                                            "des agents")
    company_id = fields.Many2one('res.company', 'Compagnie', required=True, default=1)

    def get_country_header(self):
        res = []
        employees = self.env['hr.employee'].search([('country_id', '!=', None)])
        for employee in employees:
            res.append(employee.country_id.name)
        res = sorted(list(set(res)))
        return res

    def get_country_lines(self):
        global categories
        categories = self.env['hr.category.contract'].search([], order='name')
        res_category = []
        countries = self.get_country_header()
        for category in categories:
            res_country = []
            for country in countries:
                employees_male = self.env['hr.employee'].search_count([('category_contract_id', '=', category.id),
                                                                       ('country_id.name', '=', country),
                                                                       ('gender', '=', 'male')])
                employees_female = self.env['hr.employee'].search_count([('category_contract_id', '=', category.id),
                                                                         ('country_id.name', '=', country),
                                                                         ('gender', '=', 'female')])
                gender = []
                gender_data = {
                    'male': employees_male,
                    'female': employees_female
                }

                gender.append(gender_data)
                vals_country = {
                    'country': country,
                    'gender': gender
                }
                res_country.append(vals_country)

            vals_category = {
                'category': category.name,
                'data_nationality': res_country
            }
            res_category.append(vals_category)
        return res_category

    def get_year_header(self):
        res = []
        current_year = fields.Date.today().year
        res.append(str(current_year))
        delta = 1
        for cpt in range(3):
            res.append(str(current_year - delta))
            delta += 1
        res = sorted(list(set(res)))
        return res

    def get_year_lines(self):
        res_category = []
        years = self.get_year_header()
        for category in categories:
            res_year = []
            for year in years:
                employees_male_hiring = self.env['hr.employee'].search_count(
                    [('category_contract_id', '=', category.id),
                     ('date_anciennete', '<=',
                      str(year) + '-12-31'),
                     ('gender', '=', 'male'),
                     '|', ('active', '=', True),
                     ('active', '=', False)])
                employees_male_exit = self.env['hr.employee'].search_count([('category_contract_id', '=', category.id),
                                                                            ('end_date', '<=', str(year) + '-12-31'),
                                                                            ('gender', '=', 'male'),
                                                                            '|', ('active', '=', True),
                                                                            ('active', '=', False)])

                employees_female_hiring = self.env['hr.employee'].search_count(
                    [('category_contract_id', '=', category.id),
                     ('date_anciennete', '<=',
                      str(year) + '-12-31'),
                     ('gender', '=', 'female'),
                     '|', ('active', '=', True),
                     ('active', '=', False)])
                employees_female_exit = self.env['hr.employee'].search_count(
                    [('category_contract_id', '=', category.id),
                     ('end_date', '<=',
                      str(year) + '-12-31'),
                     ('gender', '=', 'female'),
                     '|', ('active', '=', True),
                     ('active', '=', False)])
                gender = []
                gender_data = {
                    'male': employees_male_hiring - employees_male_exit,
                    'female': employees_female_hiring - employees_female_exit
                }

                gender.append(gender_data)
                vals_country = {
                    'year': year,
                    'gender': gender
                }
                res_year.append(vals_country)

            vals_category = {
                'category': category.name,
                'data_year': res_year
            }
            res_category.append(vals_category)
        return res_category

    # def get_city_header(self):
    #     res = []
    #     employees = self.env['hr.employee'].search([('agence_id', '!=', None), ('agence_id.city_id', '!=', None)])
    #     for employee in employees:
    #         res.append(employee.agence_id.city_id.name)
    #     res = sorted(list(set(res)))
    #     return res

    # def get_city_lines(self):
    #     res_category = []
    #     cities = self.get_city_header()
    #     for category in categories:
    #         res_city = []
    #         for city in cities:
    #             employees_male = self.env['hr.employee'].search_count([('category_contract_id', '=', category.id),
    #                                                                    ('agence_id', '!=', None),
    #                                                                    ('agence_id.city_id', '!=', None),
    #                                                                    ('agence_id.city_id.name', '=', city),
    #                                                                    ('gender', '=', 'male')])
    #
    #             employees_female = self.env['hr.employee'].search_count([('category_contract_id', '=', category.id),
    #                                                                      ('agence_id', '!=', None),
    #                                                                      ('agence_id.city_id', '!=', None),
    #                                                                      ('agence_id.city_id.name', '=', city),
    #                                                                      ('gender', '=', 'female')])
    #             gender = []
    #             gender_data = {
    #                 'male': employees_male,
    #                 'female': employees_female
    #             }
    #
    #             gender.append(gender_data)
    #             vals_country = {
    #                 'country': city,
    #                 'gender': gender
    #             }
    #             res_city.append(vals_country)
    #
    #         vals_category = {
    #             'category': category.name,
    #             'data_nationality': res_city
    #         }
    #         res_category.append(vals_category)
    #     return res_category

    def get_total_gross_lines(self):
        res_category = []
        years = self.get_year_header()

        for category in categories:
            res_year = []
            for year in years:
                date_from = str(year) + '-01-01'
                date_to = str(year) + '-12-31'

                select_query = """
                    SELECT 
                        SUM(pl.total)
                    FROM 
                        hr_payslip_line pl
                    INNER JOIN 
                        hr_employee emp ON emp.id = pl.employee_id
                    INNER JOIN 
                        hr_category_contract cc ON cc.id = emp.category_contract_id
                    WHERE 
                        pl.code in ('BRUT','TRSP') 
                    AND 
                        pl.date_from >= %(date_from)s 
                    AND 
                        pl.date_to <= %(date_to)s
                    AND 
                        emp.gender = %(gender)s 
                    AND 
                        cc.name = %(category)s
                    GROUP BY                         
                        cc.name                
                """
                gender = 'female'
                params_query = {
                    'date_from': date_from,
                    'date_to': date_to,
                    'gender': gender,
                    'category': category.name
                }
                self.env.cr.execute(select_query, params_query)
                data_female = self.env.cr.fetchall()
                gender = 'male'
                params_query = {
                    'date_from': date_from,
                    'date_to': date_to,
                    'gender': gender,
                    'category': category.name
                }
                self.env.cr.execute(select_query, params_query)
                data_male = self.env.cr.fetchall()
                gender = []
                gender_data = {
                    'male': data_male[0][0] if data_male else 0,
                    'female': data_female[0][0] if data_female else 0
                }

                gender.append(gender_data)
                vals_country = {
                    'year': year,
                    'gender': gender
                }
                res_year.append(vals_country)

            vals_category = {
                'category': category.name,
                'data_year': res_year
            }
            res_category.append(vals_category)
        return res_category

    def get_overall_payroll_lines(self):
        res_category = []
        years = self.get_year_header()

        for category in categories:
            res_year = []
            for year in years:
                date_from = str(year) + '-01-01'
                date_to = str(year) + '-12-31'

                select_query = """
                            SELECT 
                                SUM(pl.total)
                            FROM 
                                hr_payslip_line pl
                            INNER JOIN 
                                hr_employee emp ON emp.id = pl.employee_id
                            INNER JOIN 
                                hr_category_contract cc ON cc.id = emp.category_contract_id
                            INNER JOIN
                                hr_salary_rule sr ON sr.id = pl.salary_rule_id
                            WHERE 
                                sr.overall_payroll_rule IS True
                            AND 
                                pl.date_from >= %(date_from)s 
                            AND 
                                pl.date_to <= %(date_to)s
                            AND 
                                emp.gender = %(gender)s 
                            AND 
                                cc.name = %(category)s
                            GROUP BY                         
                                cc.name                
                        """
                gender = 'female'
                params_query = {
                    'date_from': date_from,
                    'date_to': date_to,
                    'gender': gender,
                    'category': category.name
                }
                self.env.cr.execute(select_query, params_query)
                data_female = self.env.cr.fetchall()
                gender = 'male'
                params_query = {
                    'date_from': date_from,
                    'date_to': date_to,
                    'gender': gender,
                    'category': category.name
                }
                self.env.cr.execute(select_query, params_query)
                data_male = self.env.cr.fetchall()
                gender = []
                gender_data = {
                    'male': data_male[0][0] if data_male else 0,
                    'female': data_female[0][0] if data_female else 0
                }

                gender.append(gender_data)
                vals_country = {
                    'year': year,
                    'gender': gender
                }
                res_year.append(vals_country)

            vals_category = {
                'category': category.name,
                'data_year': res_year
            }
            res_category.append(vals_category)
        return res_category

    def print_report_xls(self):
        data = {
            'country_header': self.get_country_header(),
            'country_lines': self.get_country_lines(),
            'year_header': self.get_year_header(),
            'year_lines': self.get_year_lines(),
            'city_header': '',
            'city_lines': '',
            'total_gross_header': self.get_year_header(),
            'total_gross_lines': self.get_total_gross_lines(),
            'overall_payroll_header': self.get_year_header(),
            'overall_payroll_line': self.get_overall_payroll_lines()
        }
        return self.env.ref('hr_payroll_custom.action_salary_mass_xls').report_action(self, data=data)

    def print_report_pdf(self):
        pass
