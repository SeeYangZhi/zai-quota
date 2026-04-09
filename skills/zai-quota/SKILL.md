---
name: zai-quota
description: Check Z.ai (Zhipu AI) GLM API usage quota, remaining sessions, and token limits. Use when the user asks about zai quota, GLM quota, API usage, or remaining sessions for Zhipu/Z.ai.
license: MIT
compatibility: Requires Python 3.6+ and internet access to api.z.ai or open.bigmodel.cn.
metadata:
  author: Yang Zhi See
  version: "1.1.0"
  repository: https://github.com/SeeYangZhi/zai-quota
---

# Z.ai GLM Quota Check

Check remaining quota and usage for the Z.ai (Zhipu AI) GLM Coding Plan via the monitoring API.

## How to Run

```bash
python3 skills/zai-quota/scripts/check_quota.py
python3 skills/zai-quota/scripts/check_quota.py --models
python3 skills/zai-quota/scripts/check_quota.py --models --json
```

## API Key Resolution (in priority order)

1. `ZAI_API_KEY` environment variable
2. `--key` CLI argument
3. `~/.hermes/auth.json` (Hermes Agent credential pool)

## CLI Options

```bash
python3 skills/zai-quota/scripts/check_quota.py --json
python3 skills/zai-quota/scripts/check_quota.py --key YOUR_API_KEY
python3 skills/zai-quota/scripts/check_quota.py --endpoint cn
python3 skills/zai-quota/scripts/check_quota.py --endpoint intl
python3 skills/zai-quota/scripts/check_quota.py --models
```

## Quota Mode (default)

Fetches quota from the monitoring API and shows usage %, remaining quota, and reset times.

## Models Mode (--models)

Lists all supported GLM models and runs a quick availability check per model.

### API Endpoints

- **Endpoints:**
  - International: `https://api.z.ai/api/paas/v4/models`
  - China: `https://open.bigmodel.cn/api/paas/v4/models`
- **Auth:** Bearer token
