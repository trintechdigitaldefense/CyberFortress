# Client rule-pack templates

Rule packs map **indicators → severity + playbook**. They do **not** execute containment by themselves. LIVE mode, ROE allow-list, circuit breaker, and Tier-2 WhatsApp APPROVE still gate every protective action.

## Quick select

```bash
./scripts/select_rule_pack.sh              # list + show active
./scripts/select_rule_pack.sh smb          # write CF_RULE_PACK_NAME into .env
./scripts/select_rule_pack.sh retail --restart
```

Or manually:

```bash
export CF_RULE_PACK_NAME=smb    # smb | retail | finance | default
./stop.sh && ./start.sh local
```

Dashboard shows the active pack under **Rule pack**.

## Sector packs

| Alias | File | Use when |
|-------|------|----------|
| `default` | `config/rule_packs/default.yaml` | General / first pilot |
| `smb` | `config/rule_packs/smb_v1.yaml` | SMB / small office — RDP, phishing, ransomware |
| `retail` | `config/rule_packs/retail_v1.yaml` | Retail / POS / store networks |
| `finance` | `config/rule_packs/finance_v1.yaml` | Finance / higher scrutiny |

## Custom client pack

1. Copy example overlay:
   ```bash
   mkdir -p config/tenants/acme_tt
   cp config/tenants/example_client/rule_pack.yaml config/tenants/acme_tt/rule_pack.yaml
   # edit rules for that client
   ```
2. Set tenant:
   ```bash
   export CF_TENANT_ID=acme_tt
   # or: CF_RULE_PACK=config/tenants/acme_tt/rule_pack.yaml
   ```
3. Restart stack (or systemd: `systemctl restart cyberfortress.target`).

### Tuning tips (client networks)

- **Start with sector pack**, run ≥7 days MONITORING, then add/remove indicators that match real noise.
- Prefer **specific** `match_indicators` (e.g. `rdp_bruteforce`) over broad tokens that flood Tier-2.
- Map high-impact playbooks (`isolate_endpoint`, `halt_operations`) only if they appear on the **signed ROE** allow-list.
- Keep CRITICAL rare — ransomware / confirmed C2 — so operators are not alert-fatigued.
- Document client-specific additions in the pack `description` field.

### Example rule shape

```yaml
- id: CF-CLIENT-010
  name: portal_abuse
  match_indicators: [client_portal_abuse, password_spray]
  severity: HIGH
  playbook: block_ip
```

Playbook names must match what the platform implements (`block_ip`, `isolate_endpoint`, `terminate_session`, `deploy_decoy`, `unblock_ip`, `restore_endpoint`, optional Tier-2: `subnet_isolation`, `credential_rotation`, `halt_operations`).

## Verification

```bash
./scripts/select_rule_pack.sh
python3 -c "from core.rules import pack_summary, load_pack; load_pack(force=True); print(pack_summary())"
curl -s http://127.0.0.1:8091/api/rule-packs | python3 -m json.tool
```
