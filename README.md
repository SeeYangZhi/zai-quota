# zai-quota

Check your [Z.ai](https://z.ai) (Zhipu AI / 智谱AI) GLM API usage quota, remaining sessions, and token limits from the terminal.

Zero dependencies - uses only Python stdlib.

## Quick Start

```bash
# Download
curl -O https://raw.githubusercontent.com/SeeYangZhi/zai-quota/main/zai_quota.py

# Run with your API key
ZAI_API_KEY=your_key python3 zai_quota.py
```

## Installation

No install needed - it's a single Python file. Just download and run.

```bash
# Option 1: Direct download
curl -O https://raw.githubusercontent.com/SeeYangZhi/zai-quota/main/zai_quota.py

# Option 2: Git clone
git clone https://github.com/SeeYangZhi/zai-quota.git
cd zai-quota
```

## Usage

```bash
# Set API key via environment variable
export ZAI_API_KEY="your_api_key_here"
python3 zai_quota.py

# Or pass via --key
python3 zai_quota.py --key "your_api_key_here"

# JSON output
python3 zai_quota.py --json

# Force a specific endpoint
python3 zai_quota.py --endpoint cn     # China (open.bigmodel.cn)
python3 zai_quota.py --endpoint intl    # International (api.z.ai)
```

## Output

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

## API Key Sources (in order of priority)

1. `--key` CLI argument
2. `ZAI_API_KEY` environment variable
3. `~/.hermes/auth.json` (if you use [Hermes Agent](https://github.com/nicepkg/hermes))

## How It Works

Calls the Z.ai monitoring API to fetch your current quota usage. Supports two endpoints:

- **International:** `api.z.ai` (default, tried first)
- **China:** `open.bigmodel.cn` (fallback)

> **Note:** This uses an unofficial monitoring endpoint. It works today but Z.ai could change it without notice.

## Requirements

- Python 3.6+
- A Z.ai API key (from [z.ai](https://z.ai) or [open.bigmodel.cn](https://open.bigmodel.cn))

## License

MIT
