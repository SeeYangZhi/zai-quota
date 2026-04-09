---
name: zai-quota
description: Check Z.ai (Zhipu AI) GLM API usage quota, remaining sessions, and token limits. Use when the user asks about zai quota, GLM quota, API usage, or remaining sessions for Zhipu/Z.ai.
license: MIT
compatibility: Requires Python 3.6+ and internet access to api.z.ai or open.bigmodel.cn.
metadata:
  author: Yang Zhi See
  version: "1.0.0"
  repository: https://github.com/SeeYangZhi/zai-quota
---

# Z.ai GLM Quota Check

Check remaining quota and usage for the Z.ai (Zhipu AI) GLM Coding Plan via the monitoring API.

## How to Run

```bash
python3 skills/zai-quota/scripts/check_quota.py
```

## API Key Resolution (in priority order)

1. `ZAI_API_KEY` environment variable
2. `--key` CLI argument
3. `~/.hermes/auth.json` (Hermes Agent credential pool)

## API Details

- **Endpoints:**
  - International: `https://api.z.ai/api/monitor/usage/quota/limit`
  - China: `https://open.bigmodel.cn/api/monitor/usage/quota/limit`
- **Auth:** Bearer token
- **Response:** `{ data: { limits: [...], level: "lite|standard|pro" } }`
  - Each limit has `type`, `percentage` (0 = unused, 100 = exhausted), `remaining`, and `nextResetTime`

## CLI Options

```bash
python3 skills/zai-quota/scripts/check_quota.py --json
python3 skills/zai-quota/scripts/check_quota.py --key YOUR_API_KEY
python3 skills/zai-quota/scripts/check_quota.py --endpoint cn
python3 skills/zai-quota/scripts/check_quota.py --endpoint intl
```

## Example Output

```
  Z.ai GLM Quota
  Plan: Lite
  -------------------------------------
  [green] Time Limit
     Used: 0% | Remaining: 100
       - search-prime: 0
       - web-reader: 0
       - zread: 0
     Resets: 2026-04-16 10:31 SGT

  [green] Tokens
     Used: 18%
     Resets: in 3h

  -------------------------------------
```
