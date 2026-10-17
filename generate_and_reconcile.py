"""
Affiliate Revenue Reconciliation - RevOps portfolio demo.
All data is SYNTHETIC test data generated with a fixed seed.

Reconciliation model:
- 'Tracked revenue' = commission earned per partner for the period (tracking/admin).
- Invoices are issued to partners for the earned amount.
- Payments are matched to invoices by explicit invoice reference, with
  compatible partner and currency, up to the invoice's remaining balance.
- Multiple receipts may settle one invoice (instalments). A receipt that
  cannot be allocated (no invoice, wrong partner, wrong currency, or arriving
  after the invoice is already settled) stays unallocated and is reported as
  such. Nothing is auto-allocated across unrelated invoices.

Reporting separates four distinct measures, which must not be summed together:
  1. Outstanding invoice balances (incl. partial remainders), with ageing.
  2. Unallocated receipts (unmatched cash, overpayment residuals, duplicates).
  3. Billing discrepancies (invoice total vs tracked revenue).
  4. Currency exceptions (receipts in the wrong currency, awaiting resolution).

Money is normalised to EUR for comparison using fixed demo rates; wrong
currency receipts are left unallocated rather than converted and matched.
"""
import csv, json, random, os
from collections import defaultdict
from datetime import date, timedelta

random.seed(42)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SCRIPT_DIR, "data")
os.makedirs(OUT, exist_ok=True)

TODAY = date(2026, 10, 17)
PERIOD = "2026-09"
FX = {"EUR": 1.0, "USD": 0.92, "GBP": 1.17}   # demo rates to EUR
TERMS_DAYS = 14

VERTICALS = ["Crypto", "Trading", "iGaming", "FinTech"]
MODELS = ["CPA", "RevShare", "Hybrid"]
REGIONS = ["Nordics", "DACH", "UK", "Benelux", "CEE", "APAC"]
first = ["Apex","Nordic","Vertex","Lunar","Quant","Pioneer","Harbor","Summit","Delta","Orion",
         "Atlas","Cobalt","Ember","Fjord","Granite","Helix","Ionic","Juniper","Kestrel","Larus",
         "Meridian","Nimbus","Onyx","Pike","Quartz","Ridge","Solara","Tundra","Umbra","Vega",
         "Willow","Xenon","Yarrow","Zephyr","Aurora","Basalt","Cirrus","Dune","Echo","Flint",
         "Gale","Hollow","Iris","Jade","Koto"]
suffix = ["Markets","Capital","Trade","Partners","Media","Labs","Exchange","Group","Networks","Digital"]

partners = []
for i in range(45):
    partners.append({
        "partner_id": f"P{1001+i}",
        "partner_name": f"{first[i]} {random.choice(suffix)}",
        "vertical": random.choice(VERTICALS),
        "model": random.choice(MODELS),
        "region": random.choice(REGIONS),
        "currency": random.choices(["EUR","USD","GBP"], weights=[5,4,2])[0],
    })
pmeta = {p["partner_id"]: p for p in partners}
tracked = {}
for p in partners:
    base = random.choice([1,1,1,2,2,3,5]) * random.randint(900, 7800)
    tracked[p["partner_id"]] = round(base + random.uniform(-200, 200), 2)

ids = [p["partner_id"] for p in partners]
random.shuffle(ids)
instalment    = set(ids[0:2])     # two receipts settle one invoice (must NOT be a duplicate)
short_pay     = set(ids[2:7])     # partial payment, balance remains
over_pay      = set(ids[7:9])     # overpayment residual unallocated
overdue_unpaid= set(ids[9:15])    # unpaid, varied ages
duplicate     = set(ids[15:17])   # second identical full payment -> unallocated residual
no_invoice    = set(ids[17:19])   # payment with no invoice reference
currency_err  = set(ids[19:22])   # receipt in wrong currency -> unallocated
billing_err   = set(ids[22:26])   # invoice total != tracked revenue (still paid)
mismatched_ref= set(ids[26:27])   # payment references another partner's invoice
awaiting      = set(ids[27:29])   # invoice issued, due in the future, unpaid

# issue dates to spread ageing
AGE_ISSUE = [date(2026,10,2), date(2026,9,28), date(2026,9,15),
             date(2026,8,25), date(2026,7,18), date(2026,6,20)]
SHORT_ISSUE = [date(2026,10,1), date(2026,10,1), date(2026,9,10),
               date(2026,8,20), date(2026,10,5)]

invoices = []
payments = []
pc = 5001
def add_inv(pid, issue, amt, cur):
    inv = {"invoice_id": f"INV-{PERIOD}-{pid}", "partner_id": pid, "period": PERIOD,
           "invoice_date": issue.isoformat(), "due_date": (issue+timedelta(days=TERMS_DAYS)).isoformat(),
           "invoice_amount": round(amt,2), "currency": cur}
    invoices.append(inv); return inv
def add_pay(pid, pdate, amt, cur, ref):
    global pc
    payments.append({"payment_id": f"PM{pc}", "partner_id": pid, "payment_date": pdate.isoformat(),
                     "amount_received": round(amt,2), "currency": cur, "invoice_ref": ref})
    pc += 1

age_i = 0; short_i = 0
for p in partners:
    pid = p["partner_id"]; cur = p["currency"]; trk = tracked[pid]
    std_issue = date(2026,10,1)

    if pid in no_invoice:
        add_pay(pid, date(2026,10,9), trk, cur, "")          # unmatched cash
        continue

    if pid in overdue_unpaid:
        add_inv(pid, AGE_ISSUE[age_i % len(AGE_ISSUE)], trk, cur); age_i += 1
        continue                                             # unpaid

    if pid in awaiting:
        add_inv(pid, date(2026,10,10), trk, cur)             # due 2026-10-24, not due
        continue                                             # unpaid, not yet due

    if pid in mismatched_ref:
        inv = add_inv(pid, std_issue, trk, cur)              # stays outstanding
        wrong = f"INV-{PERIOD}-{list(overdue_unpaid)[0]}"    # another partner's invoice id
        add_pay(pid, date(2026,10,8), trk, cur, wrong)
        continue

    # invoice amount (billing error keys a wrong amount)
    inv_amt = round(trk * random.choice([0.9,1.12,0.85]),2) if pid in billing_err else round(trk,2)

    if pid in short_pay:
        issue = SHORT_ISSUE[short_i % len(SHORT_ISSUE)]; short_i += 1
        inv = add_inv(pid, issue, inv_amt, cur)
        add_pay(pid, issue+timedelta(days=5), round(inv_amt*random.choice([0.6,0.75,0.8]),2), cur, inv["invoice_id"])
        continue

    inv = add_inv(pid, std_issue, inv_amt, cur)
    ref = inv["invoice_id"]; pay_date = std_issue+timedelta(days=random.randint(3,12))

    if pid in instalment:
        add_pay(pid, pay_date, round(inv_amt*0.5,2), cur, ref)
        add_pay(pid, pay_date+timedelta(days=4), round(inv_amt-round(inv_amt*0.5,2),2), cur, ref)
    elif pid in over_pay:
        add_pay(pid, pay_date, round(inv_amt*random.choice([1.1,1.05]),2), cur, ref)
    elif pid in currency_err:
        wrong_cur = "USD" if cur != "USD" else "GBP"
        add_pay(pid, pay_date, inv_amt, wrong_cur, ref)      # wrong currency -> unallocated
    elif pid in duplicate:
        add_pay(pid, pay_date, inv_amt, cur, ref)
        add_pay(pid, pay_date+timedelta(days=2), inv_amt, cur, ref)  # second full -> residual
    else:
        add_pay(pid, pay_date, inv_amt, cur, ref)            # clean, settles invoice

def write_csv(path, rows, cols):
    with open(path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
        for r in rows: w.writerow(r)

write_csv(f"{OUT}/partners.csv", partners, ["partner_id","partner_name","vertical","model","region","currency"])
write_csv(f"{OUT}/tracked_revenue.csv",
          [{"partner_id":k,"period":PERIOD,"tracked_revenue":v,"currency":pmeta[k]["currency"]} for k,v in tracked.items()],
          ["partner_id","period","tracked_revenue","currency"])
write_csv(f"{OUT}/invoices.csv", invoices, ["invoice_id","partner_id","period","invoice_date","due_date","invoice_amount","currency"])
write_csv(f"{OUT}/payments.csv", payments, ["payment_id","partner_id","payment_date","amount_received","currency","invoice_ref"])

# ===================== RECONCILIATION ENGINE =====================
def eur(a,c): return round(a*FX[c],2)
inv_by_id = {i["invoice_id"]: i for i in invoices}
remaining = {i["invoice_id"]: i["invoice_amount"] for i in invoices}
alloc_by_inv = defaultdict(float)

exceptions = []   # record-level issues
def ex(partner_id, category, record, amount_eur, currency, status, detail):
    exceptions.append({"partner_id": partner_id, "partner_name": pmeta[partner_id]["partner_name"],
                       "vertical": pmeta[partner_id]["vertical"], "category": category,
                       "record": record, "amount_eur": round(amount_eur,2), "currency": currency,
                       "status": status, "detail": detail})

# ---- payment allocation (process chronologically) ----
pay_unalloc = {}   # payment_id -> unallocated amount (native)
for pm in sorted(payments, key=lambda x: x["payment_date"]):
    amt = pm["amount_received"]; cur = pm["currency"]; ref = pm["invoice_ref"]; pid = pm["partner_id"]
    inv = inv_by_id.get(ref)
    if not ref or inv is None:
        pay_unalloc[pm["payment_id"]] = amt
        ex(pid, "Unmatched cash", pm["payment_id"], eur(amt,cur), cur, "Unallocated",
           "Payment has no matching invoice reference")
        continue
    if inv["partner_id"] != pid:
        pay_unalloc[pm["payment_id"]] = amt
        ex(pid, "Mismatched reference", pm["payment_id"], eur(amt,cur), cur, "Unallocated",
           f"Payment references {ref}, which belongs to another partner")
        continue
    if cur != inv["currency"]:
        pay_unalloc[pm["payment_id"]] = amt
        ex(pid, "Currency exception", pm["payment_id"], eur(amt,cur), cur, "Awaiting resolution",
           f"Receipt in {cur} against a {inv['currency']} invoice; left unallocated")
        continue
    avail = remaining[ref]
    a = min(amt, max(avail,0))
    alloc_by_inv[ref] += a; remaining[ref] -= a
    resid = round(amt - a, 2)
    if resid > 0.01:
        pay_unalloc[pm["payment_id"]] = resid
        cat = "Duplicate / overpayment" if avail <= 0.01 else "Overpayment"
        ex(pid, cat, pm["payment_id"], eur(resid,cur), cur, "Unallocated residual",
           "Invoice already settled; surplus receipt unallocated" if avail<=0.01
           else "Receipt exceeds invoice balance; surplus unallocated")

# ---- invoice-level assessment ----
aging = {"Not due":0.0,"1-30 days":0.0,"31-60 days":0.0,"61-90 days":0.0,"90+ days":0.0}
outstanding_eur = 0.0; overdue_eur = 0.0; overdue_count = 0
billing_delta_eur = 0.0; billing_count = 0
invoiced_eur = 0.0; collected_eur = 0.0

for inv in invoices:
    iid = inv["invoice_id"]; cur = inv["currency"]; total = inv["invoice_amount"]
    alloc = round(alloc_by_inv[iid],2); out = round(max(remaining[iid],0),2)
    pid = inv["partner_id"]; trk = tracked[pid]
    invoiced_eur += eur(total,cur); collected_eur += eur(alloc,cur)

    # billing discrepancy: invoice vs tracked revenue
    if abs(total - trk) > 0.5:
        billing_delta_eur += eur(abs(total-trk),cur); billing_count += 1
        ex(pid, "Billing discrepancy", iid, eur(abs(total-trk),cur), cur, "Review",
           f"Invoice {total:.2f} does not match tracked revenue {trk:.2f}")

    if out > 0.01:
        outstanding_eur += eur(out,cur)
        due = date.fromisoformat(inv["due_date"]); d = (TODAY-due).days
        bucket = "Not due" if d<=0 else "1-30 days" if d<=30 else "31-60 days" if d<=60 else "61-90 days" if d<=90 else "90+ days"
        aging[bucket] += eur(out,cur)
        overdue = d > 0
        if overdue: overdue_eur += eur(out,cur); overdue_count += 1
        if alloc > 0.01:
            cat, det = "Partial payment", f"Paid {alloc:.2f} of {total:.2f}; balance {out:.2f} outstanding"
            status = f"Overdue {d}d" if overdue else "Open balance"
        else:
            cat = "Overdue invoice" if overdue else "Awaiting payment"
            det = f"Unpaid; {('due in '+str(-d)+'d') if d<0 else (str(d)+'d past due')}"
            status = f"Overdue {d}d" if overdue else "Not due"
        ex(pid, cat, iid, eur(out,cur), cur, status, det)

unallocated_eur = round(sum(eur(v, next(p["currency"] for p in payments if p["payment_id"]==k)) for k,v in pay_unalloc.items()),2)
currency_exc = [e for e in exceptions if e["category"]=="Currency exception"]
currency_exc_eur = round(sum(e["amount_eur"] for e in currency_exc),2)

flagged_partners = {e["partner_id"] for e in exceptions}
clean_count = len(partners) - len(flagged_partners)
cat_counts = defaultdict(int)
for e in exceptions: cat_counts[e["category"]] += 1

by_vertical = defaultdict(float)
for inv in invoices:
    by_vertical[pmeta[inv["partner_id"]]["vertical"]] += eur(round(alloc_by_inv[inv["invoice_id"]],2), inv["currency"])

summary = {
    "period": PERIOD, "as_of": TODAY.isoformat(), "fx": FX, "terms_days": TERMS_DAYS,
    "partner_count": len(partners), "invoice_count": len(invoices), "payment_count": len(payments),
    "invoiced_eur": round(invoiced_eur,2),
    "collected_eur": round(collected_eur,2),
    "collection_rate": round(collected_eur/invoiced_eur*100,1),
    "outstanding_eur": round(outstanding_eur,2),
    "overdue_eur": round(overdue_eur,2), "overdue_count": overdue_count,
    "unallocated_eur": unallocated_eur,
    "currency_exc_eur": currency_exc_eur, "currency_exc_count": len(currency_exc),
    "billing_delta_eur": round(billing_delta_eur,2), "billing_count": billing_count,
    "clean_count": clean_count, "flagged_partner_count": len(flagged_partners),
    "exception_count": len(exceptions),
    "aging": {k: round(v,2) for k,v in aging.items()},
    "category_counts": dict(sorted(cat_counts.items(), key=lambda x:-x[1])),
    "by_vertical": {k: round(v,2) for k,v in by_vertical.items()},
    "exceptions": sorted(exceptions, key=lambda e:-e["amount_eur"]),
}
with open(f"{OUT}/summary.json","w") as f: json.dump(summary,f,indent=2)
write_csv(f"{OUT}/exceptions.csv", exceptions,
          ["partner_id","partner_name","vertical","category","record","amount_eur","currency","status","detail"])

print(f"partners {len(partners)} invoices {len(invoices)} payments {len(payments)}")
print(f"invoiced EUR {invoiced_eur:,.2f} | collected EUR {collected_eur:,.2f} | rate {summary['collection_rate']}%")
print(f"OUTSTANDING invoice balances EUR {outstanding_eur:,.2f} (overdue {overdue_eur:,.2f}, {overdue_count} inv)")
print(f"UNALLOCATED receipts EUR {unallocated_eur:,.2f}")
print(f"BILLING discrepancies {billing_count} (EUR delta {billing_delta_eur:,.2f})")
print(f"CURRENCY exceptions {len(currency_exc)} (EUR {currency_exc_eur:,.2f})")
print(f"exceptions {len(exceptions)} | clean accounts {clean_count}/{len(partners)}")
print("aging:", summary["aging"])
print("categories:", summary["category_counts"])

# rebuild dashboard in the same run (fixes 'regenerate does not rebuild')
try:
    import build_dashboard
    build_dashboard.build()
    print("dashboard rebuilt")
except Exception as e:
    print("dashboard rebuild skipped:", e)
