#!/usr/bin/env python3
"""Check Z.ai (Zhipu AI) GLM Coding Plan quota and supported models.

Usage:
    python3 zai_quota.py
    ZAI_API_KEY=xxx python3 zai_quota.py
    python3 zai_quota.py --key xxx
    python3 zai_quota.py --json
    python3 zai_quota.py --models
    python3 zai_quota.py --endpoint cn
    python3 zai_quota.py --endpoint intl
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

QUOTA_ENDPOINTS = {
    "intl": "https://api.z.ai/api/monitor/usage/quota/limit",
    "cn": "https://open.bigmodel.cn/api/monitor/usage/quota/limit",
}

MODELS_ENDPOINTS = {
    "intl": "https://api.z.ai/api/paas/v4/models",
    "cn": "https://open.bigmodel.cn/api/paas/v4/models",
}

AUTH_FILE = Path.home() / ".hermes" / "auth.json"

# Known model tiers (latest known as of 2026-04)
MODEL_TIERS = {
    "glm-4":         "4",
    "glm-4-air":     "4",
    "glm-4-airx":    "4",
    "glm-4-flash":   "4",
    "glm-4-long":    "4",
    "glm-4-plus":    "4",
    "glm-4.5":       "4.5",
    "glm-4.5-air":   "4.5",
    "glm-4.6":       "4.6",
    "glm-4.7":       "4.7",
    "glm-5":         "5",
    "glm-5-turbo":   "5",
    "glm-5.1":       "5.1",
}


def get_api_key(cli_key: Optional[str]) -> Optional[str]:
    """Resolve API key from: CLI arg > env var > Hermes auth.json."""
    if cli_key:
        return cli_key

    env_key = os.environ.get("ZAI_API_KEY")
    if env_key:
        return env_key

    if AUTH_FILE.exists():
        try:
            auth = json.loads(AUTH_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
        else:
            pool = auth.get("credential_pool", {})
            keys = pool.get("zai", auth.get("zai", []))
            for entry in keys:
                if isinstance(entry, dict):
                    token = entry.get("access_token")
                    if token:
                        return token
                elif isinstance(entry, str):
                    return entry

    return None


def fetch_json(api_key: str, endpoints: dict, endpoint: Optional[str] = None) -> dict:
    """Fetch JSON from the first reachable endpoint."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    urls = [endpoints[endpoint]] if endpoint else list(endpoints.values())

    for url in urls:
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print("Authentication failed - API key may be invalid or expired.", file=sys.stderr)
                sys.exit(1)
            if e.code == 404:
                continue
            print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError:
            continue

    print("Could not reach any Z.ai endpoint.", file=sys.stderr)
    sys.exit(1)


TYPE_LABELS = {
    "TIME_LIMIT": "Time Limit",
    "TOKENS_LIMIT": "Tokens",
    "RATE_LIMIT": "Rate Limit",
    "TIMES_LIMIT": "Requests",
    "SESSION_LIMIT": "Sessions",
}

SGT = timezone(timedelta(hours=8))


def format_reset(ts_ms: int) -> str:
    """Format a millisecond timestamp into a human-readable reset time (SGT)."""
    try:
        dt = datetime.fromtimestamp(ts_ms / 1000, tz=SGT)
        now = datetime.now(tz=SGT)
        diff = dt - now
        if diff.total_seconds() < 0:
            return "now"
        if diff.total_seconds() < 3600:
            return f"in {int(diff.total_seconds() // 60)}m"
        if diff.total_seconds() < 86400:
            return f"in {int(diff.total_seconds() // 3600)}h"
        return dt.strftime("%Y-%m-%d %H:%M SGT")
    except (OSError, ValueError):
        return "N/A"


def pct_status(pct: int) -> str:
    if pct < 50:
        return "green"
    elif pct < 80:
        return "yellow"
    else:
        return "red"


def model_tier_label(model_id: str) -> str:
    """Return a human-readable tier label for a model ID."""
    return MODEL_TIERS.get(model_id, "??")


def print_models(models_data: dict):
    """Print supported models in a human-readable table."""
    models = models_data.get("data", [])
    if not models:
        print("  No models found.")
        return

    # Sort by tier (newest first), then alphabetically
    def sort_key(m):
        mid = m.get("id", "")
        return model_tier_label(mid)

    models_sorted = sorted(models, key=sort_key)

    print("  Z.ai GLM Models")
    print("  " + "-" * 37)

    for m in models_sorted:
        mid = m.get("id", "unknown")
        created = m.get("created")
        date_str = ""
        if created:
            try:
                date_str = datetime.fromtimestamp(created, tz=SGT).strftime("%Y-%m-%d")
            except (OSError, ValueError):
                pass
        print(f"    {mid:<20} {date_str}")

    print(f"\n  Total: {len(models)} models")

    # Try quick-access test for each model
    print("\n  Quick availability check...")
    print("  " + "-" * 37)
    return models_sorted


def quick_test_models(api_key: str, models: list, endpoint: Optional[str] = None):
    """Test each model with a minimal chat completion request."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    base_url = None
    if endpoint == "cn":
        base_url = "https://open.bigmodel.cn/api/paas/v4"
    elif endpoint == "intl":
        base_url = "https://api.z.ai/api/paas/v4"
    else:
        base_url = "https://api.z.ai/api/paas/v4"

    for m in models:
        mid = m.get("id", "")
        try:
            req_body = json.dumps({
                "model": mid,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            }).encode()
            url = f"{base_url}/chat/completions"
            req = urllib.request.Request(url, data=req_body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_data = json.loads(resp.read().decode())
                if resp_data.get("choices"):
                    print(f"    [ok]     {mid}")
                else:
                    print(f"    [ok]     {mid}  (no choices)")
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"    [locked] {mid}  (plan too low)")
            elif e.code == 429:
                print(f"    [ok]     {mid}  (rate limited - accessible)")
            elif e.code == 400:
                print(f"    [n/a]    {mid}  (not a chat model)")
            else:
                try:
                    err_body = json.loads(e.read().decode())
                    msg = err_body.get("error", {}).get("message", e.reason)
                except Exception:
                    msg = e.reason
                print(f"    [err]    {mid}  (HTTP {e.code}: {msg})")
        except urllib.error.URLError:
            print(f"    [err]    {mid}  (unreachable)")
        except Exception:
            print(f"    [err]    {mid}  (unknown error)")
        # Brief pause to avoid hammering rate limits
        import time
        time.sleep(0.5)


def print_quota(data: dict):
    """Print human-readable quota summary."""
    raw = data.get("data", data)
    limits = raw.get("limits", [])
    level = raw.get("level", "Unknown")

    level_map = {"lite": "Lite", "standard": "Standard", "pro": "Pro"}
    level_str = level_map.get(level, level)

    print(f"  Z.ai GLM Quota")
    print(f"  Plan: {level_str}")
    print("  " + "-" * 37)

    if not limits:
        print("  No quota limits found.")
        return

    for lim in limits:
        ltype = lim.get("type", "UNKNOWN")
        pct = lim.get("percentage", 0)
        label = TYPE_LABELS.get(ltype, ltype.replace("_", " ").title())
        status = pct_status(pct)
        remaining = lim.get("remaining", 0)
        reset = lim.get("nextResetTime")

        print(f"  [{status}] {label}")
        print(f"     Used: {pct}%{f' | Remaining: {remaining}' if remaining else ''}")

        details = lim.get("usageDetails", [])
        if details:
            for d in details:
                model = d.get("modelCode", "?")
                u = d.get("usage", 0)
                print(f"       - {model}: {u}")

        if reset:
            print(f"     Resets: {format_reset(reset)}")
        print()

    print("  " + "-" * 37)


def main():
    parser = argparse.ArgumentParser(
        description="Check Z.ai (Zhipu AI) GLM API usage quota and supported models"
    )
    parser.add_argument("--key", "-k", help="Z.ai API key (or set ZAI_API_KEY env var)")
    parser.add_argument("--json", "-j", action="store_true", help="Output raw JSON")
    parser.add_argument("--models", "-m", action="store_true", help="List supported models")
    parser.add_argument(
        "--endpoint", "-e",
        choices=["intl", "cn"],
        help="Force a specific endpoint (intl=api.z.ai, cn=open.bigmodel.cn)"
    )
    args = parser.parse_args()

    api_key = get_api_key(args.key)
    if not api_key:
        print(
            "No Z.ai API key found.\n"
            "  Pass --key, set ZAI_API_KEY env var, or configure in Hermes auth.json.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.models:
        data = fetch_json(api_key, MODELS_ENDPOINTS, args.endpoint)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            models = print_models(data)
            if models:
                print()
                quick_test_models(api_key, models, args.endpoint)
    else:
        data = fetch_json(api_key, QUOTA_ENDPOINTS, args.endpoint)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print_quota(data)


if __name__ == "__main__":
    main()
