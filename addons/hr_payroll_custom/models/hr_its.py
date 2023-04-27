# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from itertools import groupby
import logging

_logger = logging.getLogger(__name__)


class HrITS(models.Model):
    _name = 'hr.its'
    _description = "Gestion de ITS"

    def _get_effectif_employee(self):
        slip_obj = self.env['hr.payslip']
        all_slips = slip_obj.search([('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to),
                                     ('company_id', '=', self.company_id.id)])
        total_number_local = 0
        total_number_expat = 0
        if all_slips:
            self.env.cr.execute("SELECT COUNT (distinct(id)), nature_employe FROM hr_employee WHERE "
                                "id IN (SELECT employee_id FROM hr_payslip WHERE id=ANY(%s)) "
                                "GROUP BY nature_employe", (all_slips.ids,))
            result = self.env.cr.dictfetchall()
            if result:
                for res in result:
                    if res['nature_employe'] == 'local':
                        total_number_local = res['count']
                    else:
                        total_number_expat = res['count']
        self.total_number_local = total_number_local
        self.total_number_expat = total_number_expat

    def _get_revenu_employee(self):
        slip_obj = self.env['hr.payslip']
        all_slips = slip_obj.search([('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to),
                                     ('company_id', '=', self.company_id.id)])
        local_ids = []
        expat_ids = []
        total_brut_imposable_local = 0
        total_brut_imposable_expat = 0
        try:
            if all_slips:
                self.env.cr.execute("SELECT distinct(id), nature_employe FROM hr_employee WHERE "
                                    "id IN (SELECT employee_id FROM hr_payslip WHERE id=ANY(%s)) "
                                    "GROUP BY nature_employe, id", (all_slips.ids,))
                result = self.env.cr.dictfetchall()
                if result:
                    for x in result:
                        if x['nature_employe'] == 'local':
                            local_ids.append(x['id'])
                        else:
                            expat_ids.append(x['id'])
                if local_ids != []:
                    self.env.cr.execute("SELECT sum(total) FROM hr_payslip_line WHERE slip_id=ANY(%s) AND code='BRUT'"
                                        " AND employee_id=ANY(%s)",
                                        (all_slips.ids, local_ids))
                    result = self.env.cr.fetchone()
                    if result:
                        total_brut_imposable_local = float(result[0]) * 0.8

                if expat_ids != []:
                    self.env.cr.execute("SELECT sum(total) FROM hr_payslip_line WHERE slip_id=ANY(%s) AND code='BRUT'"
                                        " AND employee_id=ANY(%s)",
                                        (all_slips.ids, expat_ids))
                    result = self.env.cr.fetchone()
                    if result:
                        total_brut_imposable_expat = float(result[0]) * 0.8
        except Exception as ex:
            _logger.error('error %s', str(ex))
        finally:
            self.total_brut_imposable_local = total_brut_imposable_local
            self.total_brut_imposable_expat = total_brut_imposable_expat

    date_from = fields.Date('Debut mois', required=True)
    date_to = fields.Date('Fin mois', required=True)
    name = fields.Char('Nom', required=True, size=155)
    company_id = fields.Many2one('res.company', 'Société', default=lambda self: self.env.user.company_id.id)
    total_brut = fields.Integer("Total Brut", default=0)
    total_avantage_nature = fields.Integer("Avantage en nature", default=0)
    total_autres = fields.Integer("Total Autres", default=0)
    revenu_net_imposable = fields.Integer("Revenu Net imposable", default=0)
    total_net_imposable = fields.Integer("Total Net imposable", default=0)
    total_cn = fields.Integer("Contribution national", default=0)
    total_cnps_employee = fields.Integer("Total Régime retraite", default=0)
    total_igr_employee = fields.Integer("Impôt Général sur le revenu (IGR)", default=0)
    total_regime_agricole = fields.Integer("Total Régime Agricole", default=0)
    total_its_employee = fields.Integer("Impôt sur traitements, salaires, pensions, rentes viagères (IS)", default=0)
    total_retenu_employee = fields.Integer("TOTAL DES RETENUES AUX SALARIES", compute='_compute_all_total', default=0)
    total_number_local = fields.Integer("Effectif locaux", compute='_get_effectif_employee', default=0)
    total_number_expat = fields.Integer("Effectif Expatriés", compute='_get_effectif_employee', default=0)
    total_brut_imposable_local = fields.Integer("Revenu Net imposable des locaux", compute='_get_revenu_employee',
                                                default=0)
    total_brut_imposable_expat = fields.Integer("Revenu Net imposable des expatriés", compute='_get_revenu_employee',
                                                default=0)
    total_ce_expat = fields.Integer("Total CE Personnel expatrié (Régime général)", compute='_compute_all_total',
                                    default=0)
    total_ce_local = fields.Integer("Total CE Personnel Local (Régime général)", default=0)
    total_ce_agricole = fields.Integer("Total CE Régime agricole", compute='_compute_all_total', default=0)
    total_cn_expat_employer = fields.Integer("Personnel expatrié (Régime général)", compute='_compute_all_total',
                                             default=0)
    total_cn_locala_employer = fields.Integer("Personnel Local (Régime général)", compute='_compute_all_total',
                                              default=0)
    total_contribution_employer = fields.Integer("TOTAL DES CONTRIBUTIONS A LA CHARGE DE L’EMPLOYEUR",
                                                 compute='_compute_all_total', default=0)
    amount_total = fields.Integer("TOTAL A PAYER", compute='_compute_all_total', default=0)

    def _compute_all_total(self):
        self.total_ce_expat = self.total_brut_imposable_expat * self.company_id.rate_ce_expat / 100
        self.total_ce_agricole = self.total_brut_imposable_expat * self.company_id.rate_ce_agricole / 100
        self.total_cn_expat_employer = self.total_brut_imposable_expat * self.company_id.rate_its / 100
        self.total_cn_locala_employer = self.total_brut_imposable_local * self.company_id.rate_its / 100
        self.total_contribution_employer = self.total_ce_expat + self.total_ce_agricole + self.total_cn_expat_employer \
                                           + self.total_cn_locala_employer
        self.amount_total = self.total_contribution_employer + self.total_retenu_employee

        self.total_retenu_employee = self.total_cnps_employee + self.total_its_employee + self.total_cn + \
                                     self.total_regime_agricole + self.total_igr_employee

    def get_payslips_by_employee(self, date_from, date_to):
        res = {}
        payslip_obj = self.env['hr.payslip']
        slip_ids = payslip_obj.search([('date_from', '>=', date_from), ('date_to', '<=', date_to)])
        emp_id_double = slip_ids.mapped(lambda r: r.employee_id.id)
        emp_ids = list(set(emp_id_double))
        if slip_ids and emp_ids:
            for e in emp_ids:
                payslips = slip_ids.search([('employee_id', '=', e)])
                res[e] = payslips
            return res

    def compute_assiette(self, payslips_by_employee):
        employee_dict = {}
        if payslips_by_employee:
            for e in payslips_by_employee.keys():
                res = {
                    'remun': 0,
                    'av_nat': 0,
                    'autre': 0,
                    'pens': 0,
                    'rente': 0,
                    'total': 0,
                    'is_expatried': 0,
                }
                payslips = payslips_by_employee[e]
                for slip in payslips:
                    if slip.contract_id.expatried is True:
                        slip_lines = slip.line_ids
                        for line in slip_lines:
                            if line.code == 'BASE_IMP':
                                res['remun'] = round(line.total)
                            if line.code == 'AVTGN':
                                res['av_nat'] = round(line.total)
                            if line.code == 'AUTRE':
                                res['autre'] = int(line.total)
                            if line.code == 'PENS':
                                res['pens'] = round(line.total)
                            if line.code == 'REN':
                                res['rente'] = int(line.total)
                        res['total'] = round(res['remun'] + res['av_nat'] + res['autre'])
                        res['is_expatried'] = True
                    if slip.contract_id.expatried is False:
                        slip_lines = slip.line_ids
                        for line in slip_lines:
                            if line.code == 'BASE_IMP':
                                res['remun'] = round(line.total)
                            if line.code == 'AVTGN':
                                res['av_nat'] = round(line.total)
                            if line.code == 'AUTRE':
                                res['autre'] = round(line.total)
                            if line.code == 'PENS':
                                res['pens'] = round(line.total)
                            if line.code == 'REN':
                                res['rente'] = round(line.total)
                        res['total'] = round(res['remun'] + res['av_nat'] + res['autre'])
                        res['is_expatried'] = False
                employee_dict[e] = res
            print(employee_dict)
            return employee_dict

    def computeTotalBrut(self, res):
        liste = []
        data = {
            'total_remu': 0,
            'total_pens': 0,
            'total_av_nat': 0,
            'total_autre': 0,
            'total_rente_1': 0,
            'total_rente_2': 0,
            'total_brut': 0,
        }
        for k in res.keys():
            liste.append(res[k])
        for l in liste:
            data['total_remu'] += l['remun']
            data['total_av_nat'] += l['av_nat']
            data['total_brut'] += l['total']
            data['total_pens'] += l['pens']
            if l['rente'] > 100000 and l['rente'] < 300000:
                data['total_rente_1'] += l['rente']
            if l['rente'] >= 300000:
                data['total_rente_2'] += l['rente']
        print(data)
        return data

    def computeRevNetImp(self, res):
        data = {
            'net_imp_brut': 0,
            'net_imp_pens': 0,
            'net_imp_rente_1': 0,
            'net_imp_rente_2': 0,
            'total': 0,
        }
        if res:
            data['net_imp_brut'] = round((res['total_brut'] * 20) / 100)
            data['net_imp_pens'] = round((res['total_pens'] * 25) / 100)
            data['net_imp_rente_1'] = round((res['total_rente_1'] * 40) / 100)
            data['net_imp_rente_2'] = round((res['total_rente_2'] * 25) / 100)
        data['total'] = data['net_imp_brut'] + data['net_imp_pens'] \
                        + data['net_imp_rente_1'] + data['net_imp_rente_2']
        print(data)
        return data

    def computeBaseImp(self, res):
        emp_dict = {}
        if res:
            for k in res.keys():
                data = {
                    'base_is': 0,
                    'montant_is': 0,
                    'base_cn': 0,
                    'montant_cn': 0,
                    'base_igr': 0,
                    'montant_igr': 0,
                }
                dico = res[k]
                part = self.env['hr.employee'].browse(k).part_igr
                data['base_is'] = dico['total']
                base = dico['total']
                data['montant_is'] = (base * 1.2) / 100
                data['base_cn'] = (base * 80) / 100
                if data['base_cn'] > 50000 and data['base_cn'] <= 130000:
                    data['montant_cn'] = round(((data['base_cn'] - 50000) * 1.5) / 100)
                if data['base_cn'] > 130001 and data['base_cn'] <= 200000:
                    data['montant_cn'] = round(((data['base_cn'] - 130000) * 5) / 100 + ((130000 - 50000) * 1.5) / 100)
                if data['base_cn'] > 200000:
                    data['montant_cn'] = round(
                        ((data['base_cn'] - 200000) * 10) / 100 + ((200000 - 130000) * 5) / 100 + (
                                (130000 - 50000) * 1.5) / 100)
                data['base_igr'] = round((base * 80) / 100 - (data['montant_is'] + data['montant_cn']))
                Q = data['base_igr'] / part
                if Q > 25000 and Q < 45583:
                    data['montant_igr'] = round((data['base_igr'] * 10) / 110 - 2273 * part)
                if Q > 45584 and Q < 81583:
                    data['montant_igr'] = round((data['base_igr'] * 15) / 115 - 4076 * part)
                if Q > 81584 and Q < 126583:
                    data['montant_igr'] = round((data['base_igr'] * 20) / 120 - 7031 * part)
                if Q > 126584 and Q < 220333:
                    data['montant_igr'] = round((data['base_igr'] * 25) / 125 - 11250 * part)
                if Q > 220334 and Q < 389083:
                    data['montant_igr'] = round((data['base_igr'] * 35) / 135 - 24306 * part)
                if Q > 389084 and Q < 842166:
                    data['montant_igr'] = round((data['base_igr'] * 45) / 145 - 44181 * part)
                if Q > 842167:
                    data['montant_igr'] = round((data['base_igr'] * 60) / 160 - 98633 * part)
                emp_dict[k] = data
        print(emp_dict)
        return emp_dict

    def computeAmountBase(self, res):
        data = {
            'base_is': 0,
            'total_is': 0,
            'total_cn': 0,
            'total_igr': 0,
            'total_base_igr': 0,
            'total': 0,
        }
        if res:
            for k in res.keys():
                data['base_is'] += res[k]['base_is']
                data['total_is'] += res[k]['montant_is']
                data['total_cn'] += res[k]['montant_cn']
                data['total_igr'] += res[k]['montant_igr']
                data['total_base_igr'] += res[k]['base_igr']
            data['total'] = round(data['total_is'] + data['total_cn'] + data['total_igr'])
            print(data)
            return data

    def computeComtributionEmp(self, res):
        data = {
            'local': 0,
            'expatried': 0,
            'Nbre_local': 0,
            'Nbre_expatried': 0,
            'CE_expatried': 0,
            'CNc_local': 0,
            'CNc_expatried': 0,
            'total': 0,
        }
        for k in res.keys():
            if res[k]['is_expatried'] == False:
                data['Nbre_local'] += 1
                data['local'] += round(res[k]['total'])
            if res[k]['is_expatried'] == True:
                data['Nbre_expatried'] += 1
                data['expatried'] += res[k]['total']
        data['CNc_local'] = round((data['local'] * 1.5) / 100)
        data['CNc_expatried'] = round((data['expatried'] * 1.5) / 100)
        data['CE_expatried'] = round((data['expatried'] * 11.5) / 100)
        data['total'] = round(data['CNc_local'] + data['CNc_expatried'] + data['CE_expatried'])
        print(data)
        return data

    def computeNetPaie(self, res1, res2):
        total = round(res1['total'] + res2['total'])
        return total

    def _print_report(self, data):

        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('hr_payroll_custom.hr_its_report').with_context(portrait=True).report_action(self,
                                                                                                         data=data,
                                                                                                         config=False)

    def check_report(self):
        self.ensure_one()
        print(self.id)
        data = {}
        data['ids'] = self.id
        data['model'] = 'hr.its'
        data['form'] = self.read(['date_from', 'date_to', 'company_id'])[0]
        slip_ids = self.get_payslips_by_employee(data['form']['date_from'], data['form']['date_to'])
        data['assiette'] = self.compute_assiette(slip_ids)
        data['TotalBrut'] = self.computeTotalBrut(data['assiette'])
        data['RevNetImp'] = self.computeRevNetImp(data['TotalBrut'])
        data['BaseImp'] = self.computeBaseImp(data['assiette'])
        data['AmountBase'] = self.computeAmountBase(data['BaseImp'])
        data['ComtributionEmp'] = self.computeComtributionEmp(data['assiette'])
        data['NetPaie'] = self.computeNetPaie(data['AmountBase'], data['ComtributionEmp'])
        return self._print_report(data)

    def compute(self):
        slip_obj = self.env['hr.payslip']
        all_slips = slip_obj.search([('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to),
                                     ('company_id', '=', self.company_id.id)])
        lines = []
        amount = 0
        if all_slips:
            total_brut = sum([slip.brut_imposable for slip in all_slips])
            self.total_brut = total_brut
            revenu_net_imposable = total_brut
            self.revenu_net_imposable = revenu_net_imposable
            total_net_imposable = revenu_net_imposable * 0.8
            self.total_net_imposable = total_net_imposable
            self.total_its_employee = self.total_net_imposable * 1.5 / 100
            self.env.cr.execute("SELECT sum(total) FROM hr_payslip_line WHERE slip_id=ANY(%s) AND code='CN'",
                                (all_slips.ids,))
            result = self.env.cr.fetchone()
            if result:
                self.total_cn = result[0]
            self.env.cr.execute(
                "SELECT sum(total) FROM hr_payslip_line WHERE slip_id=ANY(%s) AND code='CNPS'",
                (all_slips.ids,))
            result = self.env.cr.fetchone()
            if result:
                self.total_cnps_employee = result[0]
            self.env.cr.execute(
                "SELECT sum(total) FROM hr_payslip_line WHERE slip_id=ANY(%s) AND code='IGR'",
                (all_slips.ids,))
            result = self.env.cr.fetchone()
            if result:
                self.total_igr_employee = result[0]
