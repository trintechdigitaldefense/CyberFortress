(function(){
  function ensurePanel(){
    if(document.getElementById('notify-number')) return;
    const host=document.querySelector('.container')||document.body;
    const div=document.createElement('div');
    div.className='panel';
    div.style.marginTop='1rem';
    div.innerHTML=`
<div class="panel-header"><span>WhatsApp reports (settings)</span><span id="notify-status" style="font-size:.72rem;color:var(--muted)">—</span></div>
<div style="padding:.9rem 1rem 1rem">
<p style="font-size:.7rem;color:var(--muted);margin-bottom:.5rem">Register the business WhatsApp number for CyberFortress reports. Meta token stays in server .env.</p>
<div style="display:flex;flex-wrap:wrap;gap:.75rem;align-items:flex-end">
  <label style="display:flex;flex-direction:column;gap:.25rem;font-size:.72rem;color:var(--muted)">Report number (E.164)
    <input type="text" id="notify-number" placeholder="+18683620679" style="background:#0b1220;border:1px solid var(--border);color:var(--text);padding:.45rem .6rem;border-radius:8px;min-width:200px" />
  </label>
  <label style="display:flex;align-items:center;gap:.4rem;font-size:.72rem;color:var(--muted)"><input type="checkbox" id="notify-daily" checked /> Daily summary</label>
  <label style="display:flex;align-items:center;gap:.4rem;font-size:.72rem;color:var(--muted)"><input type="checkbox" id="notify-live" checked /> Live alerts (HIGH+)</label>
  <button class="btn" id="btn-save-notify" type="button">Save</button>
</div>
</div>`;
    host.appendChild(div);
    document.getElementById('btn-save-notify').onclick=async()=>{
      const btn=document.getElementById('btn-save-notify');btn.disabled=true;
      try{
        const body={
          report_to:(document.getElementById('notify-number').value||'').trim(),
          daily_enabled:!!document.getElementById('notify-daily').checked,
          live_alerts_enabled:!!document.getElementById('notify-live').checked,
          min_live_severity:'HIGH'
        };
        const j=await(await fetch('/api/settings/whatsapp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
        if(j.ok){if(window.toast)toast('WhatsApp report settings saved');else alert('Saved');}
        else if(window.toast)toast(j.error||'Save failed'); else alert(j.error||'Save failed');
      }catch(e){if(window.toast)toast('Save failed');}
      btn.disabled=false;
    };
  }
  function applyNotify(d){
    ensurePanel();
    const n=d.notify||{};
    const numEl=document.getElementById('notify-number');
    if(numEl && document.activeElement!==numEl) numEl.value=n.report_to||'';
    const dailyEl=document.getElementById('notify-daily');
    if(dailyEl && document.activeElement!==dailyEl) dailyEl.checked=!!n.daily_enabled;
    const liveEl=document.getElementById('notify-live');
    if(liveEl && document.activeElement!==liveEl) liveEl.checked=!!n.live_alerts_enabled;
    const ns=document.getElementById('notify-status');
    if(ns){
      const parts=[];
      if(n.report_to) parts.push(n.report_to);
      parts.push(n.daily_enabled?'daily on':'daily off');
      parts.push(n.live_alerts_enabled?'live on':'live off');
      ns.textContent=parts.join(' · ')||'not configured';
    }
  }
  const _fetch=window.fetch;
  window.fetch=async function(url, opts){
    const res=await _fetch.apply(this, arguments);
    try{
      if(String(url).includes('/api/status') && (!opts||!opts.method||opts.method==='GET')){
        const clone=res.clone();
        clone.json().then(applyNotify).catch(()=>{});
      }
    }catch(e){}
    return res;
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', ensurePanel);
  else ensurePanel();
})();
