# -*- coding:utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class HrDasc(models.Model):
    _name = "hr.dasc"
    _description = "Declaration annuelle des salaires et des cotisations"

    seq_dasc = fields.Char('Sequencement', readonly=True)
    date_from = fields.Date('Date debut')
    date_to = fields.Date('Date fin')
    type_cotisation = fields.Selection([('mens', 'Mensuelle'), ('trim', 'Trimestrielle')], 'type cotisation',
                                       required=True)
    company_id = fields.Many2one('res.company', 'Compagnie', required=True, default=1)

    @api.model
    def create(self, vals):

        vals['seq_dasc'] = self.env['ir.sequence'].next_by_code('hr.dasc')
        return super(HrDasc, self).create(vals)

    def compute_disa(self):
        res = {
            'assurance_maternite': 0,
            'prestation_familiale': 0,
            'accident_travail': 0,
            'restraite': 0,
        }
        disa_obj = self.env['hr.payroll.disa'].search(
            [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)])
        taux = self.env['hr.cnps.monthly'].get_taux(self.company_id)
        for dis in disa_obj:
            res['assurance_maternite'] = dis.total_cotisation_pf_am
            res['prestation_familiale'] = dis.total_cotisation_pf_am
            res['accident_travail'] = dis.total_accident
            res['restraite'] = dis.total_general_retraite
        res['annuelle_assurance_maternite'] = round(res['assurance_maternite'] * taux['maternite'] / 100)
        res['annuelle_prestation_familiale'] = round(res['prestation_familiale'] * taux['famille'] / 100)
        res['annuelle_accident_travail'] = round(res['accident_travail'] * taux['accident'] / 100)
        res['annuelle_restraite'] = round(res['restraite'] * taux['cnps'] / 100)
        res['TOTAL_3'] = round(res['annuelle_prestation_familiale'] + res['annuelle_prestation_familiale'] +
                               res['annuelle_accident_travail'] + res['annuelle_restraite'])
        return res

    def _compute(self):

        if self.type_cotisation == 'mens':
            res_mois = {
                'cotisation_janvier': 0,
                'total_brut_janvier': 0,
                'cotisation_fevrier': 0,
                'total_brut_fevrier': 0,
                'cotisation_mars': 0,
                'total_brut_mars': 0,
                'cotisation_avril': 0,
                'total_brut_avril': 0,
                'cotisation_mai': 0,
                'total_brut_mai': 0,
                'cotisation_juin': 0,
                'total_brut_juin': 0,
                'cotisation_juillet': 0,
                'total_brut_juillet': 0,
                'cotisation_aout': 0,
                'total_brut_aout': 0,
                'cotisation_septembre': 0,
                'total_brut_septembre': 0,
                'cotisation_octobre': 0,
                'total_brut_octobre': 0,
                'cotisation_novembre': 0,
                'total_brut_novembre': 0,
                'cotisation_decembre': 0,
                'total_brut_decembre': 0,
                'TOTAL_1': 0,
                'TOTAL_2': 0
            }
            mensuelles = self.env['hr.cnps.monthly'].search(
                [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)])
            for men in mensuelles:
                if men == 'janvier' or None:
                    res_mois['cotisation_janvier'] = men.total_cotisation
                    res_mois['total_brut_janvier'] = men.total_brut
                if men == 'fevrier' or None:
                    res_mois['cotisation_fevrier'] = men.total_cotisation
                    res_mois['total_brut_fevrier'] = men.total_brut
                if men == 'mars' or None:
                    res_mois['cotisation_mars'] = men.total_cotisation
                    res_mois['total_brut_mars'] = men.total_brut
                if men == 'avril':
                    res_mois['cotisation_avril'] = men.total_cotisation
                    res_mois['total_brut_avril'] = men.total_brut
                if men == 'mai' or None:
                    res_mois['cotisation_mai'] = men.total_cotisation
                    res_mois['total_brut_mai'] = men.total_brut
                if men == 'juin' or None:
                    res_mois['cotisation_juin'] = men.total_cotisation
                    res_mois['total_brut_juin'] = men.total_brut
                if men == 'juillet' or None:
                    res_mois['cotisation_juillet'] = men.total_cotisation
                    res_mois['total_brut_juillet'] = men.total_brut
                if men == 'aout' or None:
                    res_mois['cotisation_aout'] = men.total_cotisation
                    res_mois['total_brut_aout'] = men.total_brut
                if men == 'septembre' or None:
                    res_mois['cotisation_septembre'] = men.total_cotisation
                    res_mois['total_brut_septembre'] = men.total_brut
                if men == 'octobre' or None:
                    res_mois['cotisation_octobre'] = men.total_cotisation
                    res_mois['total_brut_octobre'] = men.total_brut
                if men == 'novembre' or None:
                    res_mois['cotisation_novembre'] = men.total_cotisation
                    res_mois['total_brut_novembre'] = men.total_brut
                if men == 'decembre':
                    res_mois['cotisation_decembre'] = men.total_cotisation
                    res_mois['total_brut_decembre'] = men.total_brut
            res_mois['TOTAL_1'] = res_mois['cotisation_janvier'] + res_mois['cotisation_fevrier'] + res_mois[
                'cotisation_mars'] + \
                                  res_mois['cotisation_avril'] + res_mois['cotisation_mai'] + res_mois[
                                      'cotisation_juin'] + \
                                  res_mois['cotisation_juillet'] + res_mois['cotisation_aout'] + res_mois[
                                      'cotisation_septembre'] + \
                                  res_mois['cotisation_octobre'] + res_mois['cotisation_novembre'] + res_mois[
                                      'cotisation_decembre']
            res_mois['TOTAL_2'] = res_mois['total_brut_janvier'] + res_mois['total_brut_fevrier'] + res_mois[
                'total_brut_mars'] + \
                                  res_mois['total_brut_avril'] + res_mois['total_brut_mai'] + res_mois[
                                      'total_brut_juin'] + \
                                  res_mois['total_brut_juillet'] + res_mois['total_brut_aout'] + res_mois[
                                      'total_brut_septembre'] + \
                                  res_mois['total_brut_octobre'] + res_mois['total_brut_novembre'] + res_mois[
                                      'total_brut_decembre']
            print('!!!!', res_mois)
            return res_mois

        if self.type_cotisation == 'trim':
            res = {
                'cotisation_trimestre_1': 0,
                'total_brut_trimestre_1': 0,
                'cotisation_trimestre_2': 0,
                'total_brut_trimestre_2': 0,
                'cotisation_trimestre_3': 0,
                'total_brut_trimestre_3': 0,
                'cotisation_trimestre_4': 0,
                'total_brut_trimestre_4': 0,
                'TOTAL_1': 0,
                'TOTAL_2': 0,
            }
            trimestriel = self.env['hr.cnps.trimestriel'].search(
                [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)])
            for trim in trimestriel:
                print('????', trim.trimestre, trim.total_cotisation)
                if trim == 'trimestre_1' or None:
                    res['cotisation_trimestre_1'] = trim.total_cotisation
                    res['total_brut_trimestre_1'] = trim.total_brut
                if trim == 'trimestre_2' or None:
                    res['cotisation_trimestre_2'] = trim.total_cotisation
                    res['total_brut_trimestre_2'] = trim.total_brut
                if trim == 'trimestre_3' or None:
                    res['cotisation_trimestre_3'] = trim.total_cotisation
                    res['total_brut_trimestre_3'] = trim.total_brut
                if trim == 'trimestre_4' or None:
                    res['cotisation_trimestre_4'] = trim.total_cotisation
                    res['total_brut_trimestre_4'] = trim.total_brut

            res['TOTAL_1'] = res['cotisation_trimestre_1'] + res['cotisation_trimestre_2'] + res[
                'cotisation_trimestre_3'] + res['cotisation_trimestre_4']
            res['TOTAL_2'] = res['total_brut_trimestre_1'] + res['total_brut_trimestre_2'] + res[
                'total_brut_trimestre_3'] + res['total_brut_trimestre_4']
            return res

    def _print_report(self, data):
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('hr_payroll_custom.dasc_id').with_context(landscape=True).report_action(self, data=data,
                                                                                                    config=False)

    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.id
        data['model'] = 'hr.dasc'
        data['form'] = self.read(['type_cotisation', 'date_from', 'date_to', 'company_id'])[0]
        d1 = datetime.strptime(data['form']['date_from'], '%Y-%m-%d')
        d2 = datetime.strptime(data['form']['date_to'], '%Y-%m-%d')
        if d1.month != 1 or d2.month != 12:
            raise ValidationError(_("Veuillez entrer une date d'exercice"))
        data['cnps'] = self._compute()
        data['disa'] = self.compute_disa()
        return self._print_report(data)
