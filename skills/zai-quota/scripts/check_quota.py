#!/usr/bin/env python3
"""Check Z.ai (Zhipu AI) GLM Coding Plan quota.

Usage:
    python3 zai_quota.py
    ZAI_API_KEY=xxx python3 zai_quota.py
    python3 zai_quota.py --key xxx
    python3 zai_quota.py --json
    python3 zai_quota.py --endpoint cn          # force China endpoint
    python3 zai_quota.py --endpoint intl         # force international endpoint
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

ENDPOINTS = {
    "intl": "https://api.z.ai/api/monitor/usage/quota/limit",
    "cn": "https://open.bigmodel.cn/api/monitor/usage/quota/limit",
}

AUTH_FILE = Path.home() / ".hermes" / "auth.json"


def get_api_key(cli_key: Optional[str]) -> Optional[str]:
    """Resolve API key from: CLI arg > env var > Hermes auth.json."""
    # 1. CLI argument
    if cli_key:
        return cli_key

    # 2. Environment variable
    env_key = os.environ.get("ZAI_API_KEY")
    if env_key:
        return env_key

    # 3. Hermes auth.json (for users running inside Hermes Agent)
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


def fetch_quota(api_key: str, endpoint: Optional[str] = None) -> dict:
    """Fetch quota from the monitoring API. Tries endpoints in order."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if endpoint:
        # Use a specific endpoint
        urls = [ENDPOINTS[endpoint]]
    else:
        # Try all endpoints in order
        urls = [ENDPOINTS["intl"], ENDPOINTS["cn"]]

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
                continue  # try next endpoint
            print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError:
            continue  # try next endpoint

    print("Could not reach any Z.ai quota endpoint.", file=sys.stderr)
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


def pct_emoji(pct: int) -> str:
    if pct < 50:
        return "green"
    elif pct < 80:
        return "yellow"
    else:
        return "red"


def print_human(data: dict):
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
        status = pct_emoji(pct)
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
        description="Check Z.ai (Zhipu AI) GLM API usage quota"
    )
    parser.add_argument("--key", "-k", help="Z.ai API key (or set ZAI_API_KEY env var)")
    parser.add_argument("--json", "-j", action="store_true", help="Output raw JSON")
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

    data = fetch_quota(api_key, args.endpoint)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_human(data)


if __name__ == "__main__":
    main()
