import tempfile
import unittest
from pathlib import Path
from ledger import storage, reporting, importing

class MatchingRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'demo.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_payment_does_not_match_by_amount_alone(self):
        # In seed data: MAPLE / INV-201 has amount 600.00.
        # We import a payment for HARBOR / INV-999 with amount 600.00.
        # It should NOT match MAPLE / INV-201.
        csv = 'payment_id,customer_id,invoice_number,amount\nPAY-REG-1,HARBOR,INV-999,600.00\n'
        result = importing.import_csv(self.db, csv, 'payments')
        self.assertEqual(result['imported'], 1)

        # MAPLE / INV-201 should remain unpaid (balance 600.00)
        invoices = reporting.invoices(self.db)
        maple_inv = next(r for r in invoices if r['invoice_number'] == 'INV-201')
        self.assertEqual(maple_inv['paid'], 0.0)
        self.assertEqual(maple_inv['balance'], 600.0)

        # The payment should be unmatched
        overview = reporting.overview(self.db)
        unmatched = [p for p in overview['unmatched_payments'] if p['payment_id'] == 'PAY-REG-1']
        self.assertEqual(len(unmatched), 1)

    def test_payment_matches_correct_invoice(self):
        # We import a payment for MAPLE / INV-200 with amount 100.00.
        csv = 'payment_id,customer_id,invoice_number,amount\nPAY-REG-2,MAPLE,INV-200,100.00\n'
        result = importing.import_csv(self.db, csv, 'payments')
        self.assertEqual(result['imported'], 1)

        # MAPLE / INV-200 should have 100.00 paid
        invoices = reporting.invoices(self.db)
        maple_inv = next(r for r in invoices if r['invoice_number'] == 'INV-200')
        self.assertEqual(maple_inv['paid'], 100.0)

if __name__ == '__main__':
    unittest.main()
