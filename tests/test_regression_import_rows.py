import tempfile
import unittest
from pathlib import Path
from ledger import storage, importing, reporting

class ImportRowsRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'demo.sqlite3')
        storage.seed(self.db)
        
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_invalid_row_between_valid_rows(self):
        csv = (
            "customer_id,invoice_number,amount,due_date\n"
            "HARBOR,INV-ROW-A,111.11,2026-10-02\n"
            "HARBOR,INV-ROW-B,INVALID,2026-10-03\n"
            "MAPLE,INV-ROW-C,222.22,2026-10-04\n"
        )
        res = importing.import_csv(self.db, csv, 'invoices')
        self.assertEqual(res['imported'], 2)
        self.assertEqual(res['skipped'], 0)
        self.assertEqual(res['rejected'], 1)
        self.assertEqual(res['errors'][0]['line'], 3)
        self.assertIn("amount must be a positive decimal", res['errors'][0]['reason'])

        invs = [r['invoice_number'] for r in reporting.invoices(self.db, 'all')]
        self.assertIn('INV-ROW-A', invs)
        self.assertIn('INV-ROW-C', invs)
        self.assertNotIn('INV-ROW-B', invs)

    def test_multiple_invalid_rows_with_valid_rows_around_them(self):
        csv = (
            "customer_id,invoice_number,amount,due_date\n"
            "HARBOR,INV-A,1.00,2026-10-01\n"
            "HARBOR,INV-B,BAD,2026-10-02\n"
            "HARBOR,INV-C,3.00,2026-10-03\n"
            "FAKE,INV-D,4.00,2026-10-04\n"
            "HARBOR,INV-E,5.00,2026-10-05\n"
        )
        res = importing.import_csv(self.db, csv, 'invoices')
        self.assertEqual(res['imported'], 3)
        self.assertEqual(res['rejected'], 2)
        
        invs = [r['invoice_number'] for r in reporting.invoices(self.db, 'all')]
        self.assertIn('INV-A', invs)
        self.assertIn('INV-C', invs)
        self.assertIn('INV-E', invs)

    def test_invalid_header_remains_file_level_failure(self):
        csv = (
            "wrong,header\n"
            "HARBOR,INV-X,1.00,2026-10-01\n"
        )
        with self.assertRaises(ValueError):
            importing.import_csv(self.db, csv, 'invoices')
        
        invs = [r['invoice_number'] for r in reporting.invoices(self.db, 'all')]
        self.assertNotIn('INV-X', invs)

    def test_empty_valid_csv(self):
        csv = "customer_id,invoice_number,amount,due_date\n"
        res = importing.import_csv(self.db, csv, 'invoices')
        self.assertEqual(res['imported'], 0)
        self.assertEqual(res['skipped'], 0)
        self.assertEqual(res['rejected'], 0)

if __name__ == '__main__':
    unittest.main()
