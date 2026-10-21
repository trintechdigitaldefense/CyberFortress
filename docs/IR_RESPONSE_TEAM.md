# IR Response Team (strengthened)

| Agent | Role |
|-------|------|
| **Detect** | Opens or correlates cases; scoring + min score gate |
| **Investigate** | Findings + same-target audit correlation |
| **Respond** | ROE + autonomy; awaiting_approval when live Tier-2 pending |
| **Report** | Markdown and HTML under `evidence/ir_reports/` |

## Lifecycle

`open` → `investigating` → `awaiting_approval` (optional) → `contained` → `reported` → `closed`

## Safety

Dry-run default, ROE, WhatsApp Tier-2, circuit breaker. Respond never bypasses autonomy.

## API

`GET http://127.0.0.1:8091/api/ir/cases`

## Env

```bash
CF_IR_DETECT_INTERVAL=30
CF_IR_INVESTIGATE_INTERVAL=25
CF_IR_RESPOND_INTERVAL=35
CF_IR_REPORT_INTERVAL=45
CF_IR_MIN_SCORE=55
CF_IR_RESPOND_MIN_SCORE=60
CF_IR_AUTO_RESPOND=true
CF_IR_NOTIFY_REPORTS=true
```
