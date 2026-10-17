"""Check supplied demo outputs; does not test every reconciliation rule."""
import csv
import json
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parent
summary = json.loads((BASE / 'data/summary.json').read_text())
D = lambda value: Decimal(str(value))
with (BASE / 'data/exceptions.csv').open(newline='') as stream:
    exceptions = list(csv.DictReader(stream))
assert len(exceptions) == summary['exception_count'], 'Exception count differs'
assert sum(summary['category_counts'].values()) == len(exceptions)
assert sum(D(v) for v in summary['aging'].values()) == D(summary['outstanding_eur'])
assert summary['clean_count'] + summary['flagged_partner_count'] == summary['partner_count']
html = (BASE / 'index.html').read_text()
embedded, _ = json.JSONDecoder().raw_decode(html.split('const DATA = ', 1)[1])
assert embedded == summary, 'Dashboard and summary differ'
delta = D(summary['invoiced_eur']) - D(summary['collected_eur']) - D(summary['outstanding_eur'])
print('PASS: exception counts, ageing, account counts and dashboard payload agree.')
if delta:
    print('WARNING: EUR invoiced minus allocated minus outstanding =', delta)
    print('Known conversion/rounding difference; exact financial identity is not verified.')
else:
    print('PASS: EUR invoiced equals allocated receipts plus outstanding.')
print('Scope: output consistency only, not accounting compliance or exhaustive rule tests.')
