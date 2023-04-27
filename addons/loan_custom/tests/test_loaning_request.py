import unittest
from odoo.tests import common, TransactionCase, tagged
import datetime

@tagged('post_install', '-at_install')
class TestHrLoaningRequest(common.TransactionCase):
    def setUp(self):
        super (TestHrLoaningRequest, self).setUp ()
        self.test_loaning_request = self.env['hr.loaning.request'].create({
            'employe_id':3181,
            'amount_request':50000,
            'date_request':datetime.datetime.now().date(),
            'date_deadline': datetime.datetime.now().date(),
            'reason_request':'test'

        })

    def test_action_validated(self):
        self.test_loaning_request.action_validated ()
        self.assertEqual (self.test_loaning_request.state, 'validated', "La demande est au statut validé")


if __name__ == '__main__':
    unittest.main()