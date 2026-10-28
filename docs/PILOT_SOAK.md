# Isolated VM pilot soak

**Purpose:** Exercise CyberFortress in **MONITORING** on an isolated VM long enough to trust agents, audit chain, metrics, and recovery — **before** any live containment.

This is a **release gate**. Unit tests alone are not enough.

---

## Environment rules

| Rule | Requirement |
|------|-------------|
| Isolation | Dedicated pilot VM (not production client traffic) |
| Mode | `CF_CONTAINMENT_LIVE=false` for the entire soak |
| Privileges | Root/CAP_NET_ADMIN only if you will later arm; soak itself needs normal process rights |
| Network | Synthetic or lab traffic only |
| Secrets | No production customer data; no real Meta tokens required if `whatsapp_deferred=true` |

---

## Duration

| Tier | Duration | When |
|------|----------|------|
| **Minimum** | **24 continuous hours** | Internal lab |
| **Recommended** | **72 hours** | Before paying-client LIVE |
| **Hard fail** | Any unexplained agent death loop, audit break, or metrics deadlock | Stop; fix; restart soak clock |

---

## Procedure

### Day 0 — Install and preflight

```bash
cd CyberFortress
bash scripts/pilot_vm_preflight.sh
# Must exit 0 (netadmin green). WhatsApp may be deferred.

# Monitoring only
export CF_CONTAINMENT_LIVE=false
export CF_ALLOW_FORCE=false
bash start.sh local
# Or: sudo ./deploy/systemd/install_systemd.sh && systemctl start cyberfortress.target
```

Record in ops notes:

- Host hostname, OS, kernel
- Commit SHA / version
- Preflight log path and exit code
- Operator name and start UTC time

### Soak window — daily checks

At least twice per day:

1. **Agents** — dashboard `/api/status` or heartbeats: no permanent DOWN for required agents  
2. **Metrics** — `logs/monitoring_metrics.json` updates; no deadlock (agent still responsive)  
3. **Audit** — `python3 scripts/verify_audit_chain.py` → chain intact  
4. **Disk** — logs/evidence not filling the root volume  
5. **Circuit breaker** — not stuck open without cause  
6. **Restart drill** (once per soak) — `bash stop.sh` then `bash start.sh local`; services recover  

Inject at least one **synthetic detection** (lab indicator) and confirm:

- Event appears in monitoring / recent actions  
- Case created (if IR agents running)  
- Audit entry chained  
- No live DROP applied  

### End of soak — sign-off packet

Only if all checks passed:

- [ ] Soak duration met (24h min / 72h recommended)  
- [ ] No unresolved P0 (deadlock, audit corruption, auth bypass)  
- [ ] Restart recovery verified  
- [ ] `host_netadmin_verified: true` still valid (re-run `check_netadmin.sh`)  
- [ ] Operator notes attached  

Then proceed to **legal gate** (`docs/LEGAL_GATE.md`) and only after that consider `enable_live_mode.sh`.

---

## Fail criteria (abort soak)

- Metrics or fusion hang under load  
- Audit verify fails and cannot be explained by deliberate test tamper  
- Containment armed accidentally during soak  
- Cross-tenant data bleed in multi-tenant lab  
- Secrets or `.env` committed  

---

## Related docs

- [PILOT_VM.md](PILOT_VM.md) — host and netadmin  
- [LEGAL_GATE.md](LEGAL_GATE.md) — attorney + E&O before LIVE  
- [GO_LIVE.md](GO_LIVE.md) — arming checklist  
- [OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md) — day-2 operations  
