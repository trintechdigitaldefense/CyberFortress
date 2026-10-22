# Client rule-pack templates

## Quick select

```bash
export CF_RULE_PACK_NAME=smb    # smb | retail | finance | default
./stop.sh && ./start.sh local
```

Dashboard shows the active pack under **Rule pack**.

## Files

| File | Sector |
|------|--------|
| `config/rule_packs/default.yaml` | General |
| `config/rule_packs/smb_v1.yaml` | SMB |
| `config/rule_packs/retail_v1.yaml` | Retail / POS |
| `config/rule_packs/finance_v1.yaml` | Finance |

## Custom client pack

1. Copy `config/tenants/example_client/rule_pack.yaml`
2. Place under `config/tenants/<client_id>/rule_pack.yaml`
3. Or set `rule_pack: smb` in tenant `settings.yaml`

Rule packs only **propose** actions — LIVE, ROE, breaker, and Tier-2 APPROVE still apply.
