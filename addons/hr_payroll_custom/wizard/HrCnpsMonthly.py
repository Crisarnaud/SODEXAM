#-*- coding:utf-8 -*-

from odoo import api, fields, models
from itertools import groupby
from datetime import datetime

class HrCnpsMonthly(models.TransientModel):
    _name = 'hr.cnps.monthly'
    _description = "Gestion de la CNPS MENSUEL"

    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    company_id = fields.Many2one('res.company', 'Compagnie', required=True, default=1)
    assurance_maternite = fields.Float('Assurance Maternité',compute='compute', store=True)
    prestation_familiale = fields.Float('Prestation Familiale', compute='compute', store=True)
    accident_travail = fields.Float('Accident Travail', compute='compute', store=True)
    regime_retraite = fields.Float('Régime Retraite', compute='compute', store=True)
    total_cotisation = fields.Float('Total Cotisation', compute='compute', store=True)
    total_brut = fields.Float('Total Brut',compute='compute', store=True)
    total_regime_retraite = fields.Float('Total Régime Retraite', compute='_get_totaux', store=True)
    total_des_regimes = fields.Float('Total des Régime', compute='_get_totaux', store=True)
    name = fields.Char('Sequence')
    mois = fields.Char('Mois')


    @api.model
    def create(self, vals):

        vals['name'] = self.env['ir.sequence'].next_by_code('hr.cnps.monthly')
        return super(HrCnpsMonthly, self).create(vals)

    def get_amount_by_code(self, slips, code):
        result = []
        amount = 0
        for slip in slips :
            tmp= slip.line_ids.filtered(lambda r: r.code==code)
            if tmp :
                result+= tmp
        if result :
            amount = sum([line.total for line in result])
        return amount

    def computeBrut(self, type, brut):
        vals = {}
        if type == 'm':
            if brut > 1657315:
                vals['retraite'] = 1657315
                vals['tranche']= 4
            elif brut >= 70000 and brut <= 1657315 :
                vals['retraite']= brut
                vals['tranche']= 3
            else :
                vals['retraite']= brut
                vals['tranche']= 2
            vals['autre_cotisation'] = 70000
        return vals


    def computeValues(self, employee, list_slip):
        # vals = {}
        brut = self.get_amount_by_code(list_slip, 'BRUT')
        print(brut)
        vals= self.computeBrut(employee.type, brut)

    def compute_data(self, data, tranche):
        vals = {
            'tranche': tranche,
            'nombre': 0,
            'retraite': 0,
            'cotisation': 0
        }
        for item in data:
            if item.get('tranche') == tranche:
                vals['nombre'] += 1
                vals['retraite'] += item.get('retraite')
                vals['cotisation'] += item.get('autre_cotisation')
        return vals

    def get_taux(self, company):
        if company:
            vals= {
                'accident': company.taux_accident_travail,
                'cnps': company.taux_cnps_employee_local+ company.taux_cnps_employer,
                'famille': company.taux_prestation_familiale,
                'maternite': company.taux_assurance_mater
            }
            return vals
        return {}

    def _get_totaux(self, data):
        nombre = retraite = cotisation = 0
        for item in data :
            nombre += item.get('nombre')
            retraite += item.get('retraite')
            cotisation += item.get('cotisation')
        self.total_regime_retraite = retraite
        self.total_des_regimes = cotisation
        return {
            'nombre': nombre,
            'retraite': retraite,
            'cotisation': cotisation
        }


    def compute(self):
        self.ensure_one()
        res = {}
        res['ids'] = self.id
        res['model'] = 'hr.cnps.monthly'

        data = []
        slip_obj= self.env['hr.payslip']
        slips= slip_obj.search([('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to),
                                ('company_id', '=', self.company_id.id)])
        date = fields.Datetime.from_string(self.date_from)
        print(self.mois)
        print(slips)
        data = []
        results = []
        total_brut = 0
        if slips :
            order = 0

            for employee, list_slip in groupby(slips, lambda l: l.employee_id):
                tmp = list(list_slip)
                brut = self.get_amount_by_code(tmp, 'BRUT')
                total_brut += brut
                vals = self.computeBrut(employee.type, brut)
                data.append(vals)
            for i in range(5):
                result= self.compute_data(data, i)
                results.append(result)
        res['taux'] = self.get_taux(self.company_id)
        res['lines'] = results
        res['totaux'] = self._get_totaux(results)
        res['retraite'] = round(int(res['totaux']['retraite'] * (res['taux']['cnps']/100)))
        res['accident'] = round(int(res['totaux']['cotisation'] * (res['taux']['accident']/100)))
        res['famille'] = round(int(res['totaux']['cotisation'] * (res['taux']['famille']/100)))
        res['maternity'] = round(int(res['totaux']['cotisation'] * (res['taux']['maternite']/100)))
        res['total_brut'] = total_brut
        res['name'] = self.env['ir.sequence'].next_by_code('hr.cnps.monthly')
        self.assurance_maternite = round(res['maternity'])
        self.prestation_familiale = round(res['famille'])
        self.accident_travail = round(res['accident'])
        self.regime_retraite = round(res['retraite'])
        self.total_brut = round(res['total_brut'])
        self.total_cotisation = round(int(res['maternity'] + res['famille'] + res['accident'] + res['retraite']))
        mois = date.strftime("%B")
        if mois == 'février':
            self.mois = 'fevrier'
        elif mois == 'décembre':
            self.mois = 'decembre'
        elif mois == 'août':
            self.mois = 'aout'
        else:
            self.mois = date.strftime("%B")

        return self._print_report(res)

    # hr_cnps_report

    def _print_report(self, data):
        print(data)
        # data = self.env[data['model']].browse(data.get('ids', []))
        # return self.env['web'].with_context(landscape=True).get_action(records, 'hr_payroll_ci_raport.cnps_mensuel_report', data=data)

        return self.env.ref('hr_payroll_ci_raport.hr_cnps_report').with_context(landscape=True).report_action(self, data=data, config=False)
