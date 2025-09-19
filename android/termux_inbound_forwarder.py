#!/usr/bin/env python3
"""
Termux Inbound Forwarder
- Polls Android SMS inbox via Termux:API and forwards new messages to backend /receive-sms

Requirements on the Android phone (Termux):
  pkg update && pkg install -y python termux-api
  pip install requests
  export BASE_URL=http://<YOUR_PC_LAN_IP>:8000
  python termux_inbound_forwarder.py --interval 5 --limit 50

Notes:
- Install the Termux:API companion app from F-Droid so termux-sms-* commands work.
- Ensure Termux has SMS permissions (it will prompt).
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
from typing import List, Dict

import requests


STATE_PATH = os.path.expanduser("~/.termux_inbound_state.json")


def load_state() -> Dict:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state: Dict) -> None:
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_PATH)


def hash_msg(m: Dict) -> str:
    key = f"{m.get('id')}-{m.get('number')}-{m.get('body')}-{m.get('date')}-{m.get('read')}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def inbox(limit: int = 50) -> List[Dict]:
    # termux-sms-inbox outputs JSON array
    cmd = ["termux-sms-inbox", "-l", str(limit)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"termux-sms-inbox failed: {p.stderr}")
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse inbox JSON: {e}\nOutput: {p.stdout[:300]}")


def forward(base_url: str, frm: str, body: str) -> None:
    r = requests.post(
        f"{base_url}/receive-sms",
        json={"from": frm, "message": body},
        timeout=15,
    )
    r.raise_for_status()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://127.0.0.1:8000"))
    ap.add_argument("--interval", type=int, default=5)
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    state = load_state()
    seen = set(state.get("seen", []))

    print(f"[INBOUND] Polling inbox every {args.interval}s -> {args.base_url}/receive-sms")
    try:
        while True:
            try:
                msgs = inbox(args.limit)
                # Newest last for natural processing order
                for m in reversed(msgs):
                    # Consider only inbox messages
                    if m.get("type", "").lower() != "inbox":
                        continue
                    h = hash_msg(m)
                    if h in seen:
                        continue
                    frm = m.get("number") or m.get("address") or ""
                    body = m.get("body") or ""
                    if not frm or not body:
                        continue
                    try:
                        forward(args.base_url, frm, body)
                        print(f"[INBOUND] Forwarded from {frm}: {body[:60].replace('\n',' ')}...")
                        seen.add(h)
                        # Persist a bounded history
                        if len(seen) > 1000:
                            seen = set(list(seen)[-500:])
                    except Exception as e:
                        print(f"[ERR] Forward failed: {e}")
            except Exception as e:
                print(f"[ERR] Inbox poll failed: {e}")
            state = {"seen": list(seen)}
            save_state(state)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[INBOUND] Stopped")


if __name__ == "__main__":
    main()
