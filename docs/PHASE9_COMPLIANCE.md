# Phase 9 — Compliance & legal readiness

**Not legal advice.** TrinTech must still engage counsel and maintain E&O.

## Software support

| Artifact | Purpose |
|----------|--------|
| `docs/LEGAL_GATE.md` | Attorney + E&O checklist before LIVE |
| `docs/templates/NDA_TEMPLATE.md` | NDA starting point |
| `docs/templates/ROE_TEMPLATE.md` | Rules of engagement starting point |
| `config/pilot_signoff.example.json` | Operational sign-off fields |
| `core/compliance_pack.py` | Aggregate readiness + retention + action map |
| `scripts/compliance_check.sh` | Print checklist; write `logs/compliance_report.json` |
| `core/legal_mapper.py` | Defensive CMA-oriented audit labels |
| CMA audit chain | Hash-chained evidence of actions |

## Commands

```bash
./scripts/compliance_check.sh
./scripts/readiness_check.sh --require-pilot
# Live only after soak + legal:
./scripts/enable_live_mode.sh --check
```

## Human gates (cannot be automated)

1. Signed NDA + ROE for the engagement  
2. Attorney review of ROE / liability / data handling  
3. Active E&O / cyber professional liability  
4. Documented VM soak (`docs/PILOT_SOAK.md`)  
5. Client authority to authorize defensive network actions  

## Data retention defaults

See `core.compliance_pack.retention_policy()` — override with `CF_RETENTION_*_DAYS`.
Contract wins over software defaults.
