import logging
from odoo import fields, models, api, _
import base64
import xlrd

_logger = logging.getLogger(__name__)


class ImportPrime(models.TransientModel):
    _name = 'import.prime'
    _description = 'Import primes'

    name = fields.Char()
    file_name = fields.Binary("Fichier à import", required=True)

    def _get_compute_data(self, sheet):
        try:
            keys = [sheet.cell(0, col_index).value for col_index in range(sheet.ncols)]

            dict_list = []
            for row_index in range(1, sheet.nrows):
                d = {keys[col_index]: sheet.cell(row_index, col_index).value
                     for col_index in range(sheet.ncols)}
                dict_list.append(d)
            return dict_list
        except:
            return False

    def compute_data(self):
        data_file = base64.b64decode(self.file_name)
        book = xlrd.open_workbook(file_contents=data_file)
        sheet_names = book.sheet_names()
        if sheet_names:
            for name in sheet_names:
                sheet = book.sheet_by_name(name)
                data = self._get_compute_data(sheet)
                for dt in data:
                    try:
                        identification = int(dt['identification_id'])
                        code_prime = str(dt['prime_code'])
                        amount = dt['amount']
                    except:
                        raise Warning(_("Les colonnes 'identification_id' et/ou 'amount' n'ont pas été trouvé. "
                                        "Merci de faire les corrections nécessaires"))
                    employee = self.env['hr.employee'].search([('identification_id', '=', identification)], limit=1)
                    if employee and employee.contract_id:
                        #recupérer id du contrat
                        contract = self.env['hr.contract'].search([('employee_id', '=', employee.id)], limit=1)

                        # récupérer le record de la prime en utilisant le code
                        primes = self.env['hr.payroll.prime'].search([])
                        for prime in primes:
                            if prime.code == code_prime:

                                prime_montant_obj = self.env['hr.payroll.prime.montant']
                                is_exist = prime_montant_obj.search([('prime_id', '=', prime.id),
                                                                     ('contract_id', '=', contract.id)])
                        # pour eviter les doublons dans les primes des employés
                                if is_exist:
                                    is_exist.unlink()
                                prime_montant_obj.create({
                                    'contract_id': contract.id,
                                    'prime_id': prime.id,
                                    'montant_prime': amount
                                })
                    else:
                        #mesage d'erreur
                        pass
        return True
