import json, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def build(base=None):
    base = base or SCRIPT_DIR
    d = json.load(open(os.path.join(base, "data", "summary.json")))
    payload = json.dumps(d, separators=(",", ":"))
    html = TEMPLATE.replace("__PAYLOAD__", payload)
    out = os.path.join(base, "index.html")
    open(out, "w").write(html)
    return out

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Revenue Reconciliation</title>
<meta name="description" content="Demo RevOps dashboard reconciling tracked revenue, invoices and payments across affiliate partner accounts, reporting outstanding balances, unallocated receipts, billing and currency exceptions separately.">
<style>
:root{
  --bg:#f6f7f9;--surface:#ffffff;--text:#171c27;--muted:#5c6575;--border:#e4e8ef;
  --navy:#1f2a44;--accent:#2f6df0;--pos:#1f7a5a;--warn:#9a6a12;--danger:#b23a4b;
  --warn-bg:#fdf3e1;--danger-bg:#fcebed;--pos-bg:#e8f5ef;--chip:#eef1f6;
  --shadow:0 1px 2px rgba(20,30,50,.05),0 2px 8px rgba(20,30,50,.04);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0e131d;--surface:#161c29;--text:#e7eaf1;--muted:#9aa4b6;--border:#283042;
  --navy:#c7d2ea;--accent:#5b8bff;--pos:#4cc79a;--warn:#d7a74a;--danger:#e8788a;
  --warn-bg:#2a2314;--danger-bg:#2b171b;--pos-bg:#12271f;--chip:#212a3b;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 2px 10px rgba(0,0,0,.25);
}}
:root[data-theme="dark"]{
  --bg:#0e131d;--surface:#161c29;--text:#e7eaf1;--muted:#9aa4b6;--border:#283042;
  --navy:#c7d2ea;--accent:#5b8bff;--pos:#4cc79a;--warn:#d7a74a;--danger:#e8788a;
  --warn-bg:#2a2314;--danger-bg:#2b171b;--pos-bg:#12271f;--chip:#212a3b;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 2px 10px rgba(0,0,0,.25);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:28px 16px 72px}
header.top{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px}
h1{font-size:23px;margin:0;letter-spacing:-.01em;font-weight:680}
.sub{color:var(--muted);font-size:13.5px;margin-top:3px}
.badge{display:inline-block;font-size:11.5px;color:var(--muted);border:1px solid var(--border);
  border-radius:999px;padding:3px 10px;background:var(--surface)}
.demo{font-size:11.5px;color:var(--warn);background:var(--warn-bg);border-radius:6px;padding:4px 9px;margin-top:10px;display:inline-block}
.sec-label{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:650;margin:24px 0 10px}
.grid{display:grid;gap:14px}
.kpis{grid-template-columns:repeat(4,1fr)}
@media(max-width:820px){.kpis{grid-template-columns:repeat(2,1fr)}}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;box-shadow:var(--shadow)}
.kpi .label{font-size:12px;color:var(--muted);font-weight:560;text-transform:uppercase;letter-spacing:.03em}
.kpi .val{font-size:25px;font-weight:720;margin-top:6px;letter-spacing:-.02em}
.kpi .note{font-size:12px;color:var(--muted);margin-top:3px}
.kpi.flag .val{color:var(--danger)}
.kpi.good .val{color:var(--pos)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:820px){.cols{grid-template-columns:1fr}}
h2{font-size:14px;margin:0 0 14px;font-weight:660}
.bar-row{display:grid;grid-template-columns:140px 1fr 78px;align-items:center;gap:10px;margin-bottom:9px;font-size:13px}
.track{background:var(--chip);border-radius:6px;height:16px;overflow:hidden}
.fill{display:block;height:100%;border-radius:6px;background:var(--accent)}
.fill.d{background:var(--danger)}
.bar-row .n{text-align:right;color:var(--muted);font-variant-numeric:tabular-nums}
.controls{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 10px}
.chip{border:1px solid var(--border);background:var(--surface);color:var(--muted);border-radius:999px;padding:6px 13px;font-size:12.5px;cursor:pointer;user-select:none}
.chip.active{background:var(--navy);color:var(--surface);border-color:var(--navy)}
.tablecard{padding:0;overflow:hidden}
.tbl-scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 12px;text-align:left;white-space:nowrap}
th{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);border-bottom:1px solid var(--border);cursor:pointer;position:sticky;top:0;background:var(--surface)}
td{border-bottom:1px solid var(--border)}
td.wrap-detail{white-space:normal;color:var(--muted);font-size:12px;max-width:340px}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:999px;font-weight:600}
.pill.c0{background:var(--danger-bg);color:var(--danger)}
.pill.c1{background:var(--warn-bg);color:var(--warn)}
.pill.c2{background:var(--pos-bg);color:var(--pos)}
.foot{color:var(--muted);font-size:12px;margin-top:22px;line-height:1.6}
.toggle{cursor:pointer;border:1px solid var(--border);background:var(--surface);color:var(--muted);border-radius:8px;padding:6px 11px;font-size:12.5px}
.note-sep{font-size:12px;color:var(--muted);margin-top:8px}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div>
      <h1>Affiliate Revenue Reconciliation</h1>
      <div class="sub">Tracked revenue, invoices and payments reconciled per account. Four measures reported separately, not summed.</div>
      <div class="demo" id="demo"></div>
    </div>
    <div style="display:flex;gap:8px;align-items:center">
      <span class="badge" id="pcount"></span>
      <span class="toggle" id="themeBtn">Theme</span>
    </div>
  </header>

  <div class="sec-label">Billing and collection</div>
  <div class="grid kpis" id="kpis1"></div>

  <div class="sec-label">Exceptions (distinct measures, do not add together)</div>
  <div class="grid kpis" id="kpis2"></div>

  <div class="cols" style="margin-top:16px">
    <section class="card">
      <h2>Outstanding invoice balances by age</h2>
      <div id="ageChart"></div>
      <div class="note-sep">Includes the unpaid remainder of partially paid invoices.</div>
    </section>
    <section class="card">
      <h2>Exceptions by category</h2>
      <div id="catChart"></div>
    </section>
  </div>

  <div class="sec-label">Exception queue</div>
  <div class="controls" id="filters"></div>
  <section class="card tablecard">
    <div class="tbl-scroll">
      <table id="tbl">
        <thead><tr>
          <th data-k="partner_name">Partner</th>
          <th data-k="category">Category</th>
          <th data-k="record">Record</th>
          <th class="num" data-k="amount_eur">Amount EUR</th>
          <th data-k="status">Status</th>
          <th data-k="detail">Detail</th>
        </tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </section>

  <div class="foot" id="foot"></div>
</div>

<script>
const DATA = __PAYLOAD__;
const eur = n => "€" + Math.round(n).toLocaleString("en-US");
document.querySelector("#pcount").textContent = DATA.partner_count + " partner accounts";
document.querySelector("#demo").textContent =
  "Synthetic demo data. Period " + DATA.period + ", as of " + DATA.as_of + ". EUR at fixed demo rates; wrong currency receipts left unallocated.";

const k1 = [
  {label:"Invoiced", val:eur(DATA.invoiced_eur), note:DATA.invoice_count+" invoices"},
  {label:"Collected (allocated)", val:eur(DATA.collected_eur), note:DATA.collection_rate+"% of invoiced", cls:"good"},
  {label:"Outstanding balances", val:eur(DATA.outstanding_eur), note:"unpaid + partial remainders"},
  {label:"Overdue", val:eur(DATA.overdue_eur), note:DATA.overdue_count+" invoices past due", cls:"flag"},
];
const k2 = [
  {label:"Outstanding invoice balances", val:eur(DATA.outstanding_eur), note:"receivable, by age below"},
  {label:"Unallocated receipts", val:eur(DATA.unallocated_eur), note:"unmatched cash, residuals, duplicates", cls:"flag"},
  {label:"Billing discrepancies", val:eur(DATA.billing_delta_eur), note:DATA.billing_count+" invoices vs tracked", cls:"flag"},
  {label:"Currency exceptions", val:eur(DATA.currency_exc_eur), note:DATA.currency_exc_count+" receipts awaiting resolution", cls:"flag"},
];
const tiles = (arr)=>arr.map(k=>`<div class="card kpi ${k.cls||''}"><div class="label">${k.label}</div><div class="val">${k.val}</div><div class="note">${k.note}</div></div>`).join("");
document.querySelector("#kpis1").innerHTML = tiles(k1);
document.querySelector("#kpis2").innerHTML = tiles(k2);

function bars(el, entries, danger){
  const max = Math.max(...entries.map(e=>e[1]),1);
  el.innerHTML = entries.map(([name,v,disp])=>
    `<div class="bar-row"><span>${name}</span>
     <span class="track"><span class="fill ${danger?'d':''}" style="width:${Math.max(v/max*100, v>0?3:0)}%"></span></span>
     <span class="n">${disp!==undefined?disp:v}</span></div>`).join("");
}
bars(document.querySelector("#ageChart"),
  Object.entries(DATA.aging).map(([k,v])=>[k,v,eur(v)]), true);
bars(document.querySelector("#catChart"),
  Object.entries(DATA.category_counts).map(([k,v])=>[k,v,v]), true);

const CATCLASS = {
  "Overdue invoice":"c0","Partial payment":"c0","Mismatched reference":"c0","Duplicate / overpayment":"c0",
  "Unmatched cash":"c1","Currency exception":"c1","Overpayment":"c1","Billing discrepancy":"c1","Awaiting payment":"c2"
};
let rows = DATA.exceptions.slice();
let sortK="amount_eur", sortDir=-1, filter="all";
const cats = ["all", ...Object.keys(DATA.category_counts)];
document.querySelector("#filters").innerHTML = cats.map((c,i)=>
  `<span class="chip ${i===0?'active':''}" data-f="${c}">${c==='all'?'All ('+DATA.exception_count+')':c+' ('+DATA.category_counts[c]+')'}</span>`).join("");

function render(){
  let r = rows.slice();
  if(filter!=="all") r=r.filter(x=>x.category===filter);
  r.sort((a,b)=>{let av=a[sortK],bv=b[sortK];
    return (typeof av==="string")? sortDir*av.localeCompare(bv): sortDir*(av-bv);});
  document.querySelector("#tbody").innerHTML = r.map(x=>`
    <tr>
      <td>${x.partner_name}<div style="font-size:11px;color:var(--muted)">${x.partner_id} · ${x.vertical}</div></td>
      <td><span class="pill ${CATCLASS[x.category]||'c1'}">${x.category}</span></td>
      <td style="font-variant-numeric:tabular-nums">${x.record}</td>
      <td class="num">${eur(x.amount_eur)} <span style="color:var(--muted);font-size:11px">${x.currency}</span></td>
      <td>${x.status}</td>
      <td class="wrap-detail">${x.detail}</td>
    </tr>`).join("");
}
document.querySelector("#filters").addEventListener("click",e=>{
  const c=e.target.closest(".chip"); if(!c)return;
  document.querySelectorAll(".chip").forEach(x=>x.classList.remove("active"));
  c.classList.add("active"); filter=c.dataset.f; render();
});
document.querySelectorAll("#tbl th").forEach(th=>th.addEventListener("click",()=>{
  const k=th.dataset.k; if(k===sortK) sortDir*=-1; else {sortK=k; sortDir=(k==="amount_eur")?-1:1;}
  render();
}));
render();

document.querySelector("#foot").innerHTML =
  `<b>How to read this.</b> Payments are matched to invoices by explicit reference with compatible partner and currency, up to each invoice's balance; instalments settle an invoice across several receipts. The four exception measures are different kinds of money and are shown separately: outstanding invoice balances are receivables, unallocated receipts are cash that could not be matched, billing discrepancies are invoice-versus-tracked differences, and currency exceptions are receipts in the wrong currency. ${DATA.clean_count} of ${DATA.partner_count} accounts are clean. Built from CSV sources by a Python reconciliation engine; this page is the reporting layer.`;

const root=document.documentElement;
document.querySelector("#themeBtn").addEventListener("click",()=>{
  const cur=root.getAttribute("data-theme");
  const dark=cur? cur==="dark" : matchMedia("(prefers-color-scheme:dark)").matches;
  root.setAttribute("data-theme", dark?"light":"dark");
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("wrote", build())
