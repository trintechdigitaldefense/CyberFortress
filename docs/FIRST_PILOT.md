# CyberFortress — First pilot path (end-to-end)

**TrinTech Digital Defense**  
**Model: separate WhatsApp channels** — client gets reports; only operator admins can APPROVE.

Keep **MONITORING** (`CF_CONTAINMENT_LIVE=false`) until every gate below is green.

---

## Phase 0 — Host (must be green before arming)

```bash
./install.sh
./start.sh local   # or systemd after Phase 5
./scripts/pilot_vm_preflight.sh
```

| Result | Meaning |
|--------|---------|
| **GREEN** | `config/host_capability.json` → `netadmin_ok: true`; safe path toward arming |
| **FAIL** | Stay MONITORING only on this host; fix CAP_NET_ADMIN / real VM |

See [PILOT_VM.md](PILOT_VM.md) · [HOST_REQUIREMENTS.md](HOST_REQUIREMENTS.md).

---

## Phase 1 — Legal pack (first client)

1. Copy templates; complete with counsel as needed:
   - `docs/templates/NDA_TEMPLATE.md` → signed NDA PDF  
   - `docs/templates/ROE_TEMPLATE.md` → signed ROE PDF  
2. Create sign-off:
   ```bash
   cp config/pilot_signoff.example.json config/pilot_signoff.json
   chmod 600 config/pilot_signoff.json
   ```
3. Fill **real** values (no placeholders):
   - `client_name`, `engagement_id`, `signed_by`, `client_approver`, `signoff_date_utc`
   - `roe_document` / `nda_document` = real filenames or paths of signed PDFs
   - `authorized_actions` from the signed ROE
   - `whatsapp_admins` = **TrinTech operator numbers only** (e.g. `+18683620679`)
   - `host_netadmin_verified: true` only after Phase 0 green
   - Until Meta is live: `whatsapp_deferred: true`
   - After Meta live + TLS verified: `whatsapp_tls_verified: true`, `whatsapp_deferred: false`
4. Dashboard: set **client report number** (separate from admins) for daily + live alerts.

---

## Phase 2 — Dry-run pilot week (no live DROP)

```bash
bash scripts/pilot_dry_run.sh
```

Expected chain: **seed → fusion → audit entry → evidence pack → “ready for pilot review.”**

Client WhatsApp (report number) may receive **daily** status if Meta is configured; **no** DROP rules while unarmed.

Checklist: [PILOT_DEPLOYMENT.md](PILOT_DEPLOYMENT.md).

---

## Phase 3 — Arm only after sign-off

```bash
./scripts/enable_live_mode.sh --check
./scripts/enable_live_mode.sh --enable   # type exactly: ENABLE LIVE MODE
./stop.sh && ./start.sh
```

If `check_netadmin` fails at enable time → **refused**. Stay MONITORING.

---

## Phase 4 — Operator runbook drill

```bash
bash scripts/operator_drill.sh
```

Proves Tier‑2 reaches **admin** numbers only; client report number is **not** an approver.

Details: [OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md).

---

## Phase 5 — After first pilot

| Item | Action |
|------|--------|
| Rule packs | `config/rule_packs/{retail,finance,smb}_v1.yaml` |
| systemd 24/7 | `deploy/systemd/install_systemd.sh` |
| ROE language | Use [CAPACITY.md](CAPACITY.md) limits |

---

## Short path

**credentials + green VM preflight + signed ROE → dry-run pilot → arm → operator drill**

*Defend. Detect. Dominate.*
