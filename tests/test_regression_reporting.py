import tempfile
import unittest
import shutil
from pathlib import Path
from ledger import storage, reporting

ROOT = Path(__file__).resolve().parent.parent

class ReportingRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / 'demo.sqlite3'
        fixture = ROOT / 'fixtures' / 'existing-register.sqlite3'
        shutil.copy2(fixture, self.db_path)
        self.db = storage.connect(self.db_path)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_status_all(self):
        invoices = reporting.invoices(self.db, 'all')
        self.assertEqual(len(invoices), 9)

    def test_status_open(self):
        invoices = reporting.invoices(self.db, 'open')
        self.assertEqual(len(invoices), 7)
        for inv in invoices:
            self.assertEqual(inv['status'], 'open')
            self.assertGreater(inv['balance'], 0)

    def test_status_paid(self):
        invoices = reporting.invoices(self.db, 'paid')
        self.assertEqual(len(invoices), 2)
        for inv in invoices:
            self.assertEqual(inv['status'], 'paid')
            self.assertLessEqual(inv['balance'], 0)
        
        # Verify no overlap between open and paid
        open_ids = {r['id'] for r in reporting.invoices(self.db, 'open')}
        paid_ids = {r['id'] for r in invoices}
        self.assertTrue(open_ids.isdisjoint(paid_ids))

    def test_invoices_are_ordered_by_due_date(self):
        invoices = reporting.invoices(self.db, 'all')
        for i in range(len(invoices) - 1):
            self.assertLessEqual(invoices[i]['due_date'], invoices[i+1]['due_date'])

if __name__ == '__main__':
    unittest.main()
