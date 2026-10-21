# CyberFortress quality status

**Snapshot:** v0.3.11 (2026-10-21)

## Scorecard (honest)

| Area | Score | Notes |
|------|-------|-------|
| Safety defaults | **9/10** | LIVE off, ROE, breaker, force off, bind guards |
| Monitoring | **8/10** | Fusion + host logs + metrics + rules packs |
| IR team | **7.5/10** | Detect→report pipeline; rules-driven not SIEM-class |
| Containment | **7/10** | Solid on real VM + netadmin; weak in restricted containers |
| Operator UX | **8/10** | One-command start, dashboard, health, evidence packs |
| WhatsApp live | **5/10** | Code ready; needs Meta creds + TLS (human) |
| Enterprise scale | **4/10** | SMB/pilot fit; not multi-region SOC |
| Docs / legal templates | **8/10** | Pilot, ROE, NDA, go-live clear |

**Overall for local business pilots:** **~7.5–8/10** on a real Linux VM with preflight green.  
**Overall as “enterprise AI SOC”:** **do not claim** — rules-driven tiered response only.

## Green for

- Dry-run / MONITORING pilots
- WhatsApp-deferred engagements
- Edge/gateway Linux hosts with iptables

## Not green until human steps

- Live Meta WhatsApp + TLS
- Signed NDA/ROE + pilot_signoff.json
- Live arm after `enable_live_mode.sh --check`

## Quick verify

```bash
bash scripts/quality_check.sh
bash scripts/pilot_vm_preflight.sh
./start.sh local && ./start.sh status
```
