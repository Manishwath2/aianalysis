from __future__ import annotations

import json
import sys
from typing import Any

import httpx

BASE = "http://127.0.0.1:8000"


def _print(title: str, value: Any) -> None:
    print(f"\n== {title} ==")
    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        print(value)


def main() -> int:
    ok = True

    with httpx.Client(timeout=20) as client:
        r = client.get(f"{BASE}/healthz")
        _print("healthz", {"status": r.status_code, "json": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text})
        ok &= r.status_code == 200

        r = client.get(f"{BASE}/v1/llm/providers")
        _print("/v1/llm/providers", {"status": r.status_code, "json": r.json()})
        ok &= r.status_code == 200

        r = client.get(f"{BASE}/v1/llm/models", params={"provider": "demo"})
        _print("/v1/llm/models?provider=demo", {"status": r.status_code, "json": r.json()})
        ok &= r.status_code == 200

        r = client.get(f"{BASE}/v1/models", params={"provider": "demo"})
        _print("/v1/models?provider=demo", {"status": r.status_code, "json": r.json()})
        ok &= r.status_code == 200

        payload = {
            "provider": "demo",
            "messages": [{"role": "user", "content": "hello from chunk 3"}],
        }
        r = client.post(f"{BASE}/v1/chat/completions", json=payload)
        _print("/v1/chat/completions", {"status": r.status_code, "json": r.json()})
        ok &= r.status_code == 200

    # SSE streaming test
    stream_payload = {"provider": "demo", "message": "hello sse"}
    lines: list[str] = []
    with httpx.stream("POST", f"{BASE}/v1/chat/sessions/test/stream", json=stream_payload, timeout=20) as r:
        lines.append(f"status={r.status_code} content-type={r.headers.get('content-type')}")
        for line in r.iter_lines():
            if line:
                lines.append(line)
            if len(lines) >= 30:
                break

    _print("/v1/chat/sessions/test/stream (first lines)", lines)
    ok &= any(l.startswith("event: meta") for l in lines) and any(l.startswith("event: done") for l in lines)

    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
