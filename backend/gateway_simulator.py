"""Gateway Simulator
Polls backend outbound queue and 'sends' SMS by printing them.
Marks them sent via /gateway/mark-sent.

Usage:
  python gateway_simulator.py --base-url http://localhost:8000 --interval 5

Stop with Ctrl+C.
"""
from __future__ import annotations
import time
import argparse
import requests
from typing import List


def fetch_outbound(base_url: str, limit: int = 20):
    r = requests.get(f"{base_url}/gateway/outbound", params={"limit": limit}, timeout=10)
    r.raise_for_status()
    return r.json()

def mark_sent(base_url: str, ids: List[int]):
    r = requests.post(f"{base_url}/gateway/mark-sent", json=ids, timeout=10)
    r.raise_for_status()
    return r.json()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--interval", type=int, default=5, help="Polling interval seconds")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    print(f"[SIM] Starting gateway simulator polling {args.base_url} every {args.interval}s")
    try:
        while True:
            try:
                msgs = fetch_outbound(args.base_url, args.limit)
                if msgs:
                    print(f"[SIM] Found {len(msgs)} outbound messages")
                    to_mark = []
                    for m in msgs:
                        print(f"[SEND] -> {m['phone']}: {m['body']}")
                        to_mark.append(m['id'])
                    res = mark_sent(args.base_url, to_mark)
                    print(f"[SIM] Marked sent: {res}")
                else:
                    print("[SIM] No messages.")
            except requests.RequestException as e:
                print(f"[ERR] Request failed: {e}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[SIM] Stopped.")

if __name__ == "__main__":
    main()
