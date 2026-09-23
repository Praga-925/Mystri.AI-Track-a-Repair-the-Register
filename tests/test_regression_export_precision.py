import tempfile
import unittest
import csv
import io
from pathlib import Path
from ledger import storage, importing, reporting

class ExportPrecisionRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'demo.sqlite3')
        storage.seed(self.db)
        
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _import_and_get_export(self, amount):
        csv_in = f"customer_id,invoice_number,amount,due_date\nHARBOR,INV-EXPORT-TEST,{amount},2026-10-05\n"
        importing.import_csv(self.db, csv_in, 'invoices')
        
        csv_out = reporting.export_csv(self.db)
        reader = csv.DictReader(io.StringIO(csv_out))
        for row in reader:
            if row['invoice_number'] == 'INV-EXPORT-TEST':
                return row
        return None

    def test_amount_1_13_is_preserved(self):
        row = self._import_and_get_export("1.13")
        self.assertIsNotNone(row)
        self.assertEqual(row['amount'], "1.13")
        self.assertEqual(row['paid'], "0.00")
        self.assertEqual(row['balance'], "1.13")

    def test_multiple_cent_values(self):
        cases = ["1.01", "1.05", "1.10", "1.11", "1.13", "10.99", "600.00"]
        
        for i, val in enumerate(cases):
            csv_in = f"customer_id,invoice_number,amount,due_date\nHARBOR,INV-MULTI-{i},{val},2026-10-05\n"
            importing.import_csv(self.db, csv_in, 'invoices')

        csv_out = reporting.export_csv(self.db)
        reader = csv.DictReader(io.StringIO(csv_out))
        exported_vals = {}
        for row in reader:
            if row['invoice_number'].startswith('INV-MULTI-'):
                exported_vals[row['invoice_number']] = row['amount']
                
        for i, val in enumerate(cases):
            self.assertEqual(exported_vals[f"INV-MULTI-{i}"], val)

    def test_paid_and_balance_values(self):
        # Insert invoice 10.99
        csv_in = "customer_id,invoice_number,amount,due_date\nHARBOR,INV-BAL-TEST,10.99,2026-10-05\n"
        importing.import_csv(self.db, csv_in, 'invoices')
        # Insert payment 1.13
        pay_in = "payment_id,customer_id,invoice_number,amount\nPAY-BAL-1,HARBOR,INV-BAL-TEST,1.13\n"
        importing.import_csv(self.db, pay_in, 'payments')
        
        csv_out = reporting.export_csv(self.db)
        reader = csv.DictReader(io.StringIO(csv_out))
        for row in reader:
            if row['invoice_number'] == 'INV-BAL-TEST':
                self.assertEqual(row['amount'], "10.99")
                self.assertEqual(row['paid'], "1.13")
                self.assertEqual(row['balance'], "9.86")

    def test_existing_export_structure(self):
        csv_out = reporting.export_csv(self.db)
        reader = csv.DictReader(io.StringIO(csv_out))
        self.assertEqual(reader.fieldnames, ['customer_id', 'invoice_number', 'amount', 'paid', 'balance', 'status'])
        
        rows = list(reader)
        self.assertGreater(len(rows), 0)

if __name__ == '__main__':
    unittest.main()
