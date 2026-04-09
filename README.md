# zai-quota

Check your [Z.ai](https://z.ai) (Zhipu AI / 智谱AI) GLM API usage quota, remaining sessions, and token limits.

- **Standalone CLI:** Single Python file, zero dependencies
- **Agent Skill:** Install across 45+ AI agents via `npx skills`
- **Python Tool:** Install via `uvx` or `pip`

## Quick Start

### As a standalone script

```bash
curl -O https://raw.githubusercontent.com/SeeYangZhi/zai-quota/main/zai_quota.py
ZAI_API_KEY=your_key python3 zai_quota.py
```

### As an agent skill

```bash
npx skills add SeeYangZhi/zai-quota
```

Works with Claude Code, Codex, OpenCode, Cursor, Windsurf, Gemini CLI, and [45+ agents](https://skills.sh).

### As a Python tool

```bash
# With uv
uvx zai-quota

# With pip
pip install zai-quota
zai-quota
```

---

## Standalone Usage

```bash
# Environment variable
export ZAI_API_KEY="your_api_key_here"
python3 zai_quota.py

# CLI argument
python3 zai_quota.py --key "your_api_key_here"

# JSON output
python3 zai_quota.py --json

# Force a specific endpoint
python3 zai_quota.py --endpoint cn     # China (open.bigmodel.cn)
python3 zai_quota.py --endpoint intl   # International (api.z.ai)
```

## Skill Usage

Once installed via `npx skills add SeeYangZhi/zai-quota`, compatible agents will load this skill automatically when you ask things like:

- "Check my zai quota"
- "How much GLM API usage do I have left?"
- "What's my Zhipu quota?"

The agent will run:

```bash
python3 skills/zai-quota/scripts/check_quota.py
```

## API Key Sources (in priority order)

1. `--key` CLI argument
2. `ZAI_API_KEY` environment variable
3. `~/.hermes/auth.json` (if you use [Hermes Agent](https://github.com/nicepkg/hermes))

## Output Example

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

## How It Works

Calls the Z.ai monitoring API to fetch your current quota usage. Supports two endpoints:

- **International:** `api.z.ai` (default, tried first)
- **China:** `open.bigmodel.cn` (fallback)

> **Note:** This uses an unofficial monitoring endpoint. It works today but Z.ai could change it without notice.

## Requirements

- Python 3.6+
- A Z.ai API key (from [z.ai](https://z.ai) or [open.bigmodel.cn](https://open.bigmodel.cn))

## Repository Structure

```
├── zai_quota.py               # Standalone script (root-level)
├── pyproject.toml             # uv/pip packaging
├── skills/
│   └── zai-quota/
│       ├── SKILL.md           # Agent Skills spec
│       └── scripts/
│           └── check_quota.py # Skill entrypoint
├── README.md
└── LICENSE
```

## For maintainers

```bash
make sync          # Copy zai_quota.py into skills/zai-quota/scripts/
make verify-sync   # CI check that both copies are identical
make build         # uv build
make publish       # uv build + uv publish to PyPI
```

## License

MIT
