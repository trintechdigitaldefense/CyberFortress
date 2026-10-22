# Client rule-pack templates

```bash
export CF_RULE_PACK_NAME=smb      # or retail | finance | default
./stop.sh && ./start.sh local
```

| Pack | Use for |
|------|---------|
| `default` | General baseline |
| `smb` | Small business / single site |
| `retail` | Stores / POS-adjacent |
| `finance` | Credit unions / financial SMBs |
