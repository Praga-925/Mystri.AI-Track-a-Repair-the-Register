import tempfile
import unittest
from pathlib import Path
from ledger import storage, importing, reporting

class IdempotencyRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'demo.sqlite3')
        storage.seed(self.db)
        
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_identical_invoice_is_skipped(self):
        csv = 'customer_id,invoice_number,amount,due_date\nHARBOR,INV-IDEMPOTENCY,100.00,2026-10-01\n'
        res1 = importing.import_csv(self.db, csv, 'invoices')
        self.assertEqual(res1['imported'], 1)
        self.assertEqual(res1['skipped'], 0)
        
        # Second identical import
        res2 = importing.import_csv(self.db, csv, 'invoices')
        self.assertEqual(res2['imported'], 0)
        self.assertEqual(res2['skipped'], 1)
        self.assertEqual(res2['rejected'], 0)
        
        # Verify only one exists
        invs = [r for r in reporting.invoices(self.db, 'all') if r['invoice_number'] == 'INV-IDEMPOTENCY']
        self.assertEqual(len(invs), 1)

    def test_changed_amount_is_rejected(self):
        csv1 = 'customer_id,invoice_number,amount,due_date\nHARBOR,INV-IDEMPOTENCY,100.00,2026-10-01\n'
        importing.import_csv(self.db, csv1, 'invoices')
        
        csv2 = 'customer_id,invoice_number,amount,due_date\nHARBOR,INV-IDEMPOTENCY,200.00,2026-10-01\n'
        res = importing.import_csv(self.db, csv2, 'invoices')
        
        self.assertEqual(res['imported'], 0)
        self.assertEqual(res['skipped'], 0)
        self.assertEqual(res['rejected'], 1)
        
        invs = [r for r in reporting.invoices(self.db, 'all') if r['invoice_number'] == 'INV-IDEMPOTENCY']
        self.assertEqual(invs[0]['amount'], 100.00)

    def test_changed_due_date_is_rejected(self):
        csv1 = 'customer_id,invoice_number,amount,due_date\nHARBOR,INV-IDEMPOTENCY,100.00,2026-10-01\n'
        importing.import_csv(self.db, csv1, 'invoices')
        
        csv2 = 'customer_id,invoice_number,amount,due_date\nHARBOR,INV-IDEMPOTENCY,100.00,2026-11-01\n'
        res = importing.import_csv(self.db, csv2, 'invoices')
        self.assertEqual(res['rejected'], 1)
        
        invs = [r for r in reporting.invoices(self.db, 'all') if r['invoice_number'] == 'INV-IDEMPOTENCY']
        self.assertEqual(invs[0]['due_date'], '2026-10-01')

    def test_identity_remains_case_sensitive(self):
        csv1 = 'customer_id,invoice_number,amount,due_date\nHARBOR,INV-CASE,100.00,2026-10-01\n'
        importing.import_csv(self.db, csv1, 'invoices')
        
        csv2 = 'customer_id,invoice_number,amount,due_date\nHARBOR,inv-case,100.00,2026-10-01\n'
        res = importing.import_csv(self.db, csv2, 'invoices')
        self.assertEqual(res['imported'], 1)
        
        invs = [r for r in reporting.invoices(self.db, 'all') if r['invoice_number'].upper() == 'INV-CASE']
        self.assertEqual(len(invs), 2)

    def test_whitespace_trimming(self):
        csv1 = 'customer_id,invoice_number,amount,due_date\nHARBOR,INV-TRIM,100.00,2026-10-01\n'
        importing.import_csv(self.db, csv1, 'invoices')
        
        csv2 = 'customer_id,invoice_number,amount,due_date\n  HARBOR  ,  INV-TRIM  ,100.00,2026-10-01\n'
        res = importing.import_csv(self.db, csv2, 'invoices')
        self.assertEqual(res['skipped'], 1)

if __name__ == '__main__':
    unittest.main()
