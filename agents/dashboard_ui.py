"""CyberFortress dashboard HTML UI."""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CyberFortress — Protection Dashboard</title>
<style>
:root{--bg:#0b1220;--card:#151e2e;--border:#2a364a;--text:#e8eef7;--muted:#8b9bb4;--accent:#3b82f6;--green:#22c55e;--red:#ef4444;--amber:#f59e0b}
*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
header{background:linear-gradient(135deg,#0f172a,#1e293b);border-bottom:1px solid var(--border);padding:1rem 1.25rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.6rem}
h1{font-size:1.15rem}h1 span{color:var(--accent)}.client{font-size:.8rem;color:var(--muted)}
.badge{padding:.28rem .65rem;border-radius:999px;font-size:.7rem;font-weight:700;text-transform:uppercase}
.badge.live,.badge.closed,.badge.healthy{background:rgba(34,197,94,.18);color:var(--green)}
.badge.dry,.badge.degraded{background:rgba(245,158,11,.18);color:var(--amber)}
.badge.open,.badge.unhealthy{background:rgba(239,68,68,.18);color:var(--red)}
.badge.unknown{background:rgba(139,155,180,.15);color:var(--muted)}
.btn{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:.4rem .85rem;font-size:.78rem;font-weight:600;cursor:pointer}
.btn.ghost{background:transparent;border:1px solid var(--border);color:var(--text)}.btn:disabled{opacity:.5}
.container{max-width:1200px;margin:0 auto;padding:1rem}
.banner{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1rem;margin-bottom:1rem}
.mode-title{font-weight:700;font-size:1.05rem}.mode-help{color:var(--muted);font-size:.85rem;margin-top:.25rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:.75rem;margin-bottom:1rem}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:.9rem}
.card h3{font-size:.65rem;text-transform:uppercase;color:var(--muted);margin-bottom:.3rem}
.card .value{font-size:1.15rem;font-weight:700}.card .sub{font-size:.72rem;color:var(--muted);margin-top:.15rem}
.tabs{display:flex;gap:.35rem;flex-wrap:wrap;margin-bottom:.7rem}
.tab{background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:999px;padding:.3rem .7rem;font-size:.72rem;cursor:pointer;font-weight:600}
.tab.active{background:rgba(59,130,246,.2);border-color:var(--accent);color:#fff}
.panels{display:grid;grid-template-columns:1.2fr .9fr;gap:.85rem}@media(max-width:900px){.panels{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.panel-header{padding:.7rem 1rem;border-bottom:1px solid var(--border);font-weight:600;font-size:.85rem;display:flex;justify-content:space-between}
.panel-body{max-height:380px;overflow-y:auto}
table{width:100%;border-collapse:collapse;font-size:.8rem}
th,td{padding:.5rem .8rem;text-align:left;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--muted);font-size:.65rem;text-transform:uppercase;position:sticky;top:0;background:var(--card)}
tr.row{cursor:pointer}tr.row:hover{background:rgba(59,130,246,.06)}
tr.detail td{background:rgba(15,23,42,.55);color:var(--muted);font-size:.75rem}
.sev.CRITICAL{color:var(--red);font-weight:700}.sev.HIGH{color:var(--amber);font-weight:700}.sev.INFO{color:var(--accent)}
.empty{padding:1.5rem;text-align:center;color:var(--muted)}
.agents{display:flex;flex-wrap:wrap;gap:.35rem;padding:.75rem}
.agent-chip{border:1px solid var(--border);border-radius:8px;padding:.35rem .55rem;font-size:.7rem}
.agent-chip .ok{color:var(--green)}.issues{padding:.7rem 1rem;font-size:.78rem;color:var(--amber)}
.toast{position:fixed;bottom:1rem;right:1rem;background:#0f172a;border:1px solid var(--border);padding:.7rem 1rem;border-radius:10px;font-size:.82rem;display:none;z-index:50;max-width:24rem}
.toast.show{display:block}footer{text-align:center;padding:1.2rem;color:var(--muted);font-size:.7rem}
.pulse{width:8px;height:8px;border-radius:50%;background:var(--green);display:inline-block;margin-right:.35rem;animation:p 1.6s infinite}@keyframes p{50%{opacity:.35}}
a.link{color:var(--accent);text-decoration:none}a.link:hover{text-decoration:underline}
</style></head><body>
<header>
<div><h1>CYBER<span>FORTRESS</span></h1><div class="client" id="client-label">Protection status</div></div>
<div style="display:flex;gap:.4rem;align-items:center;flex-wrap:wrap">
<span id="mode-badge" class="badge dry">MONITORING</span>
<span id="wd-badge" class="badge unknown">PLATFORM —</span>
<span id="audit-badge" class="badge unknown">AUDIT —</span>
<span id="breaker-badge" class="badge closed">BREAKER CLOSED</span>
<button class="btn ghost" id="btn-copy" type="button">Copy summary</button>
<button class="btn" id="btn-evidence" type="button">Evidence pack</button>
<button class="btn ghost" id="btn-refresh" type="button">Refresh</button>
</div></header>
<div class="container">
<div class="banner"><div class="mode-title"><span class="pulse"></span><span id="mode-val">—</span></div>
<div class="mode-help" id="mode-help">Loading…</div>
<div style="font-size:.78rem;color:var(--muted);margin-top:.4rem">Updated <span id="updated">—</span> · Auto-refresh 5s</div></div>
<div class="grid">
<div class="card"><h3>Platform</h3><div class="value" id="wd-val">—</div><div class="sub" id="wd-sub">Watchdog</div></div>
<div class="card"><h3>Audit chain</h3><div class="value" id="audit-val">—</div><div class="sub" id="audit-sub">Integrity</div></div>
<div class="card"><h3>Containment policy</h3><div class="value" style="font-size:1rem" id="policy-val">—</div><div class="sub" id="policy-sub">Allow-listed actions</div></div>
<div class="card"><h3>Circuit breaker</h3><div class="value" id="breaker-val">—</div><div class="sub" id="breaker-reason">—</div></div>
<div class="card"><h3>Waiting on you</h3><div class="value" id="pending-val">0</div><div class="sub">Approvals</div></div>
<div class="card"><h3>Actions</h3><div class="value" id="actions-val">0</div><div class="sub" id="sev-breakdown">—</div></div>
<div class="card"><h3>WhatsApp</h3><div class="value" style="font-size:1rem" id="wa-val">—</div><div class="sub">HITL channel</div></div>
<div class="card"><h3>IR team</h3><div class="value" style="font-size:1rem" id="ir-val">—</div><div class="sub" id="ir-sub">open cases</div></div>
<div class="card"><h3>Firewall</h3><div class="value" style="font-size:1rem" id="fw-val">—</div><div class="sub" id="fw-sub">CF_BLOCK chain</div></div>
</div>
<div class="tabs" id="sev-tabs">
<button class="tab active" data-sev="ALL" type="button">All</button>
<button class="tab" data-sev="CRITICAL" type="button">Critical</button>
<button class="tab" data-sev="HIGH" type="button">High</button>
<button class="tab" data-sev="INFO" type="button">Info</button>
</div>
<div class="panels">
<div class="panel"><div class="panel-header"><span>Recent protective actions</span><span style="font-size:.72rem;color:var(--muted)">Tap for details</span></div>
<div class="panel-body"><table><thead><tr><th>When</th><th>Action</th><th>Target</th><th>Level</th></tr></thead>
<tbody id="actions-body"><tr><td colspan="4" class="empty">Loading…</td></tr></tbody></table></div></div>
<div class="panel">
<div class="panel-header">Pending WhatsApp approvals</div>
<div class="panel-body"><table><thead><tr><th>Request</th><th>Action</th><th>Target</th></tr></thead>
<tbody id="pending-body"><tr><td colspan="3" class="empty">None waiting</td></tr></tbody></table></div>
<div class="panel-header" style="border-top:1px solid var(--border)">Evidence packs</div>
<div class="panel-body"><table><thead><tr><th>Pack</th><th>Size</th><th></th></tr></thead>
<tbody id="packs-body"><tr><td colspan="3" class="empty">None yet — use Evidence pack</td></tr></tbody></table></div>
<div class="panel-header" style="border-top:1px solid var(--border)">Active firewall rules (CF_BLOCK)</div>
<div class="panel-body"><table><thead><tr><th>#</th><th>Source</th><th>Dest</th><th>Action</th></tr></thead>
<tbody id="fw-rules-body"><tr><td colspan="4" class="empty">No CF rules yet</td></tr></tbody></table>
<div class="issues" id="fw-msg" style="display:block;color:var(--muted)"></div></div>
<div class="panel-header" style="border-top:1px solid var(--border);border-bottom:0">Agent heartbeats</div>
<div class="agents" id="agents-box"></div>
<div class="issues" id="issues-box" style="display:none"></div></div>
</div></div>
<footer>CyberFortress · TrinTech Digital Defense · Authorized defensive use only</footer>
<div class="toast" id="toast"></div>
<script>
let LAST=null,FILTER='ALL',OPEN_ROW=null;
function fmtTime(iso){if(!iso)return'—';try{return new Date(iso).toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'})}catch(e){return iso}}
function toast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),4500)}
function setBadge(el,text,cls){el.textContent=text;el.className='badge '+cls}
function esc(s){return String(s||'').replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>').replace(/"/g,'"')}
function renderActions(actions){const ab=document.getElementById('actions-body');const filtered=(actions||[]).filter(a=>FILTER==='ALL'||(a.severity||'')===FILTER);
if(!filtered.length){ab.innerHTML='<tr><td colspan="4" class="empty">No actions in this view yet</td></tr>';return}
ab.innerHTML=filtered.map((a,i)=>{const id='a'+i;const just=esc(a.legislative_justification||'—');const open=OPEN_ROW===id;
return `<tr class="row" onclick="toggleRow('${id}')"><td>${fmtTime(a.timestamp)}</td><td><code>${esc(a.action||'—')}</code></td><td>${esc(a.target||'—')}</td><td class="sev ${esc(a.severity||'')}">${esc(a.severity||'—')}</td></tr>
<tr class="detail" id="${id}" style="display:${open?'table-row':'none'}"><td colspan="4"><strong>Why:</strong> ${just}<br><span style="opacity:.75">Hash: ${esc((a.entry_hash||'').slice(0,16))}…</span></td></tr>`}).join('')}
function toggleRow(id){OPEN_ROW=OPEN_ROW===id?null:id;if(LAST)renderActions(LAST.recent_actions||[])}
function renderPacks(packs){const pb=document.getElementById('packs-body');
if(!packs||!packs.length){pb.innerHTML='<tr><td colspan="3" class="empty">None yet — click Evidence pack</td></tr>';return}
pb.innerHTML=packs.map(p=>{const kb=Math.max(1,Math.round((p.size_bytes||0)/1024));
return `<tr><td style="font-size:.72rem">${esc(p.name)}</td><td>${kb} KB</td><td><a class="link" href="/api/evidence/download?name=${encodeURIComponent(p.name)}">Download</a></td></tr>`}).join('')}
async function refresh(){try{const d=await(await fetch('/api/status')).json();LAST=d;
document.getElementById('client-label').textContent=(d.client_name||'Client')+' · protection status';
const live=!!d.containment_live;document.getElementById('mode-val').textContent=d.mode_label||'—';document.getElementById('mode-help').textContent=d.mode_help||'';
setBadge(document.getElementById('mode-badge'),live?'ACTIVE':'MONITORING',live?'live':'dry');
const wd=(d.watchdog&&d.watchdog.overall)||'UNKNOWN';document.getElementById('wd-val').textContent=wd;
document.getElementById('wd-sub').textContent=(d.watchdog&&d.watchdog.critical_count?d.watchdog.critical_count+' critical · ':'')+(d.watchdog&&d.watchdog.warning_count?d.watchdog.warning_count+' warnings':'Self-check OK');
setBadge(document.getElementById('wd-badge'),'PLATFORM '+wd,wd==='HEALTHY'?'healthy':wd==='DEGRADED'?'degraded':wd==='UNHEALTHY'?'unhealthy':'unknown');
const ai=d.audit_integrity||{};document.getElementById('audit-val').textContent=ai.ok?'OK':'CHECK';
document.getElementById('audit-sub').textContent=ai.message||'Integrity';
setBadge(document.getElementById('audit-badge'),ai.ok?'AUDIT OK':'AUDIT CHECK',ai.ok?'healthy':'unhealthy');
const pol=d.policy||d.roe||{};const acts=pol.authorized_actions||[];
document.getElementById('policy-val').textContent=(pol.action_count!=null?pol.action_count:acts.length)+' actions';
document.getElementById('policy-sub').textContent=pol.scope||'Allow-listed containment only';
const cb=d.circuit_breaker||{};document.getElementById('breaker-val').textContent=cb.state||'—';
document.getElementById('breaker-reason').textContent=cb.reason||(cb.state==='CLOSED'?'Normal':'—');
setBadge(document.getElementById('breaker-badge'),'BREAKER '+(cb.state||'—'),cb.state==='OPEN'?'open':'closed');
document.getElementById('pending-val').textContent=d.stats.pending_approvals;document.getElementById('actions-val').textContent=d.stats.total_actions_shown;
const sev=d.stats.by_severity||{};document.getElementById('sev-breakdown').textContent=`C:${sev.CRITICAL||0} H:${sev.HIGH||0} I:${sev.INFO||0}`;
document.getElementById('wa-val').textContent=d.whatsapp_enabled?'Connected':'Not connected';
const ir=d.ir||{}; const irs=ir.summary||{};
const openN=irs.open_total!=null?irs.open_total:(ir.open_cases||[]).length;
const irEl=document.getElementById('ir-val'); if(irEl) irEl.textContent=openN+' open';
const irSub=document.getElementById('ir-sub'); if(irSub){const by=irs.by_status||{}; irSub.textContent=Object.keys(by).map(k=>k+':'+by[k]).slice(0,4).join(' · ')||'detect → investigate → respond → report'}
const fw=d.firewall||{};document.getElementById('fw-val').textContent=fw.live_mode?'ARMED':(fw.iptables_present===false?'N/A':'Standby');
document.getElementById('fw-sub').textContent=(fw.chain||'CF_BLOCK')+' · '+(fw.rule_count||0)+' rules';
const fwb=document.getElementById('fw-rules-body');const rules=fw.rules||[];
fwb.innerHTML=rules.length?rules.map(r=>`<tr><td>${esc(r.num||'')}</td><td>${esc(r.source||'—')}</td><td>${esc(r.destination||'—')}</td><td>${esc(r.target||r.raw||'')}</td></tr>`).join(''):'<tr><td colspan="4" class="empty">No CF rules yet</td></tr>';
const fwm=document.getElementById('fw-msg');if(fwm){fwm.textContent=(fw.message||'')+(fw.warning?' · '+fw.warning:'')};
document.getElementById('updated').textContent=fmtTime(d.timestamp);
renderActions(d.recent_actions||[]);renderPacks(d.evidence_packs||[]);
const pb=document.getElementById('pending-body');pb.innerHTML=(!d.pending_approvals||!d.pending_approvals.length)?'<tr><td colspan="3" class="empty">No approvals waiting</td></tr>':d.pending_approvals.map(p=>`<tr><td style="font-family:monospace;font-size:.7rem">${esc(p.request_id||'—')}</td><td>${esc(p.action||'—')}</td><td>${esc(p.target||'—')}</td></tr>`).join('');
const agents=d.agents||{},box=document.getElementById('agents-box'),names=Object.keys(agents);
box.innerHTML=names.length?names.map(n=>{let age='—';try{age=Math.round((Date.now()-new Date(agents[n].timestamp).getTime())/1000)+'s ago'}catch(e){}return `<div class="agent-chip"><strong>${esc(n)}</strong><br><span class="ok">● ${age}</span></div>`}).join(''):'<span class="empty">No heartbeats</span>';
const issues=(d.watchdog&&d.watchdog.issues)||[],ib=document.getElementById('issues-box');
if(issues.length){ib.style.display='block';ib.innerHTML=issues.map(i=>`• [${esc(i.severity)}] ${esc(i.message)}`).join('<br>')}else{ib.style.display='none';ib.innerHTML=''}
}catch(e){console.error(e);toast('Could not refresh')}}
document.getElementById('sev-tabs').addEventListener('click',ev=>{const t=ev.target.closest('.tab');if(!t)return;FILTER=t.dataset.sev;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===t));if(LAST)renderActions(LAST.recent_actions||[])});
document.getElementById('btn-refresh').onclick=()=>{refresh();toast('Refreshed')};
document.getElementById('btn-copy').onclick=()=>{if(!LAST)return;const s=[`CyberFortress — ${LAST.client_name||'Client'}`,`Mode: ${LAST.mode_label}`,`Platform: ${(LAST.watchdog&&LAST.watchdog.overall)||'—'}`,`Audit: ${((LAST.audit_integrity&&LAST.audit_integrity.ok)?'OK':'CHECK')}`,`Policy actions: ${((LAST.policy&&LAST.policy.action_count)!=null?LAST.policy.action_count:((LAST.roe&&LAST.roe.authorized_actions)||[]).length)}`,`Breaker: ${(LAST.circuit_breaker&&LAST.circuit_breaker.state)||'—'}`,`Firewall: ${((LAST.firewall&&LAST.firewall.mode_label)||'—')} rules=${(LAST.firewall&&LAST.firewall.rule_count)||0}`,`IR open: ${((LAST.ir&&LAST.ir.summary&&LAST.ir.summary.open_total)!=null?LAST.ir.summary.open_total:((LAST.ir&&LAST.ir.open_cases)||[]).length)}`,`Actions: ${LAST.stats.total_actions_shown}`,`Pending: ${LAST.stats.pending_approvals}`,`Time: ${LAST.timestamp}`].join('\n');navigator.clipboard.writeText(s).then(()=>toast('Summary copied')).catch(()=>toast(s))};
document.getElementById('btn-evidence').onclick=async()=>{const btn=document.getElementById('btn-evidence');btn.disabled=true;try{const j=await(await fetch('/api/evidence',{method:'POST'})).json();
if(j.ok){const n=j.actions_loaded!=null?j.actions_loaded:'?';const name=(j.path||'').split('/').pop();toast(`Pack ready (${n} actions) → ${name||'evidence/'}`);refresh()}else toast(j.error||'Failed')}catch(e){toast('Evidence request failed')}btn.disabled=false};
refresh();setInterval(refresh,5000);
</script></body></html>
"""
