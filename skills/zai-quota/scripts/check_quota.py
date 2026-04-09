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

# Plan-to-model mapping from https://z.ai/subscribe
# Updated as of 2026-04
PLAN_MODELS = {
    "lite": {
        "GLM-5.1", "GLM-5-Turbo", "GLM-4.7", "GLM-4.6", "GLM-4.5-Air",
        "GLM-4.6V",
    },
    "standard": {  # Pro
        "GLM-5.1", "GLM-5-Turbo", "GLM-4.7", "GLM-4.6", "GLM-4.5-Air",
        "GLM-5", "GLM-5-Code", "GLM-4.5",
        "GLM-4.6V", "GLM-5V-Turbo",
    },
    "pro": {  # Max
        "GLM-5.1", "GLM-5-Turbo", "GLM-4.7", "GLM-4.6", "GLM-4.5-Air",
        "GLM-5", "GLM-5-Code", "GLM-4.5",
        "GLM-4.6V", "GLM-5V-Turbo",
    },
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


def build_model_list(models_data: dict, plan: str = "") -> list:
    """Merge API-returned models with plan-based model list."""
    api_ids = set()
    models = []
    for m in models_data.get("data", []):
        mid = m.get("id", "")
        api_ids.add(mid.lower())
        models.append({"id": mid, "object": "model", "created": m.get("created"), "source": "api"})

    # Add all known models that the API didn't return
    allowed = set()
    for pk in PLAN_MODELS:
        for m in PLAN_MODELS[pk]:
            allowed.add(m.lower())

    for mid_lower in allowed:
        if mid_lower not in api_ids:
            models.append({"id": mid_lower, "object": "model", "created": None, "source": "plan"})

    return models


def print_models(models_data: dict, plan: str = ""):
    """Print supported models grouped by access status."""
    models = build_model_list(models_data, plan)
    if not models:
        print("  No models found.")
        return

    # Determine which models the current plan grants
    plan_key = plan.lower() if plan else ""
    plan_set = set()
    if plan_key and plan_key in PLAN_MODELS:
        plan_set = PLAN_MODELS[plan_key]

    # Sort alphabetically
    models.sort(key=lambda m: m.get("id", "").lower())

    plan_map = {"lite": "Lite", "standard": "Pro", "pro": "Max"}
    plan_label = plan_map.get(plan_key, plan or "Unknown")

    print(f"  Z.ai GLM Models")
    print(f"  Plan: {plan_label}")
    print("  " + "-" * 40)

    accessible = []
    not_accessible = []
    for m in models:
        mid = m.get("id", "")
        has_access = mid.lower() in {x.lower() for x in plan_set} if plan_set else None
        entry = {
            "id": mid,
            "source": m.get("source", "api"),
            "created": m.get("created"),
            "access": has_access,
        }
        if has_access is True:
            accessible.append(entry)
        elif has_access is False:
            not_accessible.append(entry)
        else:
            # No plan detected, list all as unknown
            accessible.append(entry)

    # Show accessible models
    for e in accessible:
        mid = e["id"]
        tag = ""
        if e["source"] == "plan":
            tag = " *"
        date_str = ""
        if e["created"]:
            try:
                date_str = datetime.fromtimestamp(e["created"], tz=SGT).strftime("%Y-%m-%d")
            except (OSError, ValueError):
                pass
        access = "[ok]     "
        print(f"    {access} {mid:<16} {date_str}{tag}")

    # Show models on higher plans
    if not_accessible:
        print(f"\n  Available on higher plans:")
        for e in not_accessible:
            mid = e["id"]
            # Find which plan has this
            for pk, pmodels in PLAN_MODELS.items():
                if mid.lower() in {x.lower() for x in pmodels}:
                    upgrade = plan_map.get(pk, pk)
                    print(f"    [locked] {mid:<16} requires {upgrade}")
                    break

    print(f"\n  Total: {len(models)} models")
    if plan_set:
        print(f"  {len(accessible)} accessible on your plan, {len(not_accessible)} require upgrade")
    else:
        print("  * Not returned by /v4/models API, known from plan")

    return models


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
        # Fetch both models list and quota (for plan detection)
        models_data = fetch_json(api_key, MODELS_ENDPOINTS, args.endpoint)
        try:
            quota_data = fetch_json(api_key, QUOTA_ENDPOINTS, args.endpoint)
            plan = quota_data.get("data", quota_data).get("level", "")
        except SystemExit:
            plan = ""

        if args.json:
            merged = build_model_list(models_data, plan)
            print(json.dumps(merged, indent=2))
        else:
            print_models(models_data, plan)
    else:
        data = fetch_json(api_key, QUOTA_ENDPOINTS, args.endpoint)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print_quota(data)


if __name__ == "__main__":
    main()
