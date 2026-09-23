# Track A — Repair the Register: Handover

## 1. Candidate Details

- Name: Pragatishvar A
- Email used for application: praga.jv@gmail.com
- Chosen track: Track A
- Approximate total time: 4 hours (10:00 AM – 2:00 PM)

## 2. Why I Chose Track A

I chose Track A because I enjoy investigating problems, researching their root causes, and debugging issues in existing systems. I was particularly interested in understanding how the seeded defects affected the register's behavior, reproducing those issues, identifying their underlying causes, and then implementing and verifying targeted fixes. The debugging and investigation-oriented nature of this track matched the way I like to approach technical problems.

## 3. Run

Restore the supplied fixture:
```text
python restore_fixture.py --replace
```

Start the application:
```text
python app.py
```

Run the automated tests:
```text
python -m unittest discover -s tests -v
```

## 4. Verification

- **Invoice status filtering**: `python -m unittest tests.test_regression_reporting`
- **Payment matching**: `python -m unittest tests.test_regression_matching`
- **Invoice idempotency**: `python -m unittest tests.test_regression_idempotency`
- **Mixed-row CSV import**: `python -m unittest tests.test_regression_import_rows`
- **Export precision**: `python -m unittest tests.test_regression_export_precision`
- **Browser import feedback**: Verified through implementation inspection and API-level checks; automated browser testing was unavailable.
- **Chronological invoice ordering**: `python -m unittest tests.test_regression_reporting`

## 5. Repairs Delivered

### 1. Invoice Status Filtering
Before: The status filter mapped both open and paid requests to paid, causing the open filter to return paid invoices.
After: The requested status is filtered directly, correctly separating open and paid invoices.
Evidence: all=9, open=7, paid=2; open and paid sets are disjoint. (`tests/test_regression_reporting.py`)

### 2. Payment Matching
Before: A payment could match an invoice solely based on amount, even when the customer and invoice identity did not match.
After: Matching requires customer_id + invoice_number. Wrong identities remain unmatched.
Evidence: (`tests/test_regression_matching.py`)

### 3. Invoice Idempotency
Before: Repeated identical invoices were inserted again, and existing identities accepted changed details.
After: Identical imports skipped, changed details rejected, original record preserved. Case-sensitive and whitespace handling enforced.
Evidence: (`tests/test_regression_idempotency.py`)

### 4. Browser Import Feedback
Before: The browser ignored HTTP responses, falsely reporting success on errors.
After: The frontend checks HTTP responses, displays actual counts, reports API errors, and refreshes. Automated browser testing was unavailable; verified through implementation inspection and API-level checks.

### 5. Export Precision
Before: Export values were truncated, causing values such as 1.13 to be exported incorrectly as 1.12.
After: Export preserves the expected two-decimal representation.
Evidence: (`tests/test_regression_export_precision.py`)

### 6. Invalid CSV Row Handling
Before: An invalid data row caused the entire import to fail instead of allowing valid rows to continue.
After: Valid rows continue processing; invalid rows rejected individually with line number and reason.
Evidence: (`tests/test_regression_import_rows.py`)

## 6. Test Evidence

Verified final result:
- 24 tests passed
- 0 failures
- 0 errors
- 0 skipped
Regression suite covers repaired behaviors and the chronological-ordering improvement.

## 7. Existing Register Verification

Verified final state:
- 9 invoices
- 5 payments
- 7 open invoices
- 2 paid invoices
- INR 3,698.19 outstanding
- KEEP-U1 remains unmatched
- export contains header plus 9 invoice records
Supplied fixtures were preserved.

## 8. Custom Input Case

File: `samples/test_mixed.csv`
Contains: one valid invoice row, one invalid invoice row, one valid invoice row.
Verified result: HTTP 200. Imported: 2, Skipped: 0, Rejected: 1; line 3 was rejected because of an invalid amount.
Demonstrates row-level error isolation: valid rows continue processing when another data row is invalid.

## 9. Additional Improvement

Chronological invoice ordering. Invoices ordered by `due_date ASC`, with `id ASC` as deterministic tie-breaker. Verified via regression test.

## 10. Limitations

Automated browser/UI testing was unavailable in the environment, so the browser import-feedback behavior was verified through implementation inspection and API-level checks rather than automated browser testing.

## 11. AI / Tool Judgment

1. Suggestion → amount-based payment matching as a fallback → Decision → rejected because BUSINESS_RULES.md requires customer_id + invoice_number identity → Check → reproduced a same-amount/wrong-identity payment and verified it remained unmatched.
2. Suggestion → application/storage-level invoice idempotency → Decision → implemented identity checks without changing the public API → Check → verified identical imports are skipped and changed details are rejected.
3. Suggestion → process CSV rows individually → Decision → moved normalization/error handling into the row-processing loop → Check → verified valid rows are imported while invalid rows are rejected individually.

## 12. Next Step

The next highest-value step would be continued regression coverage or automated browser testing if more development time were available.
