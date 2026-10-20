# Multi-tenant config root

Each client can have a directory under `config/tenants/<tenant_id>/`.

```bash
export CF_TENANT_ID=example_client
export CF_AUDIT_PATH=./logs/tenants/example_client/cma_audit.jsonl
export CF_EVIDENCE_DIR=./evidence/tenants/example_client
```

Optional files: `rule_pack.yaml`, `settings.yaml`, `pilot_signoff.json`.

```bash
cp -r config/tenants/example_client config/tenants/acme_tt
export CF_TENANT_ID=acme_tt
./start.sh local
```

One process tree per tenant is recommended for pilots.
