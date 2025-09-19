#!/usr/bin/env python3
"""
Termux SMS Sender
- Polls backend outbound queue
- Sends using termux-sms-send (Termux:API required)
- Marks messages as sent

Usage on Android (Termux):
  pkg update && pkg install -y python termux-api
  pip install requests
  export BASE_URL=http://<YOUR_PC_LAN_IP>:8000
  python termux_sender.py --interval 10 --limit 20

Grant SMS permissions to Termux if prompted.
"""
import os
import time
import subprocess
import argparse
import requests


def fetch_outbound(base_url, limit=20):
    r = requests.get(f"{base_url}/gateway/outbound", params={"limit": limit}, timeout=15)
    r.raise_for_status()
    return r.json()


def mark_sent(base_url, ids):
    r = requests.post(f"{base_url}/gateway/mark-sent", json=ids, timeout=15)
    r.raise_for_status()
    return r.json()


def send_sms(number, body):
    # termux-sms-send -n <number> "body"
    cmd = ["termux-sms-send", "-n", number, body]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"termux-sms-send failed: {result.stderr}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://127.0.0.1:8000"))
    ap.add_argument("--interval", type=int, default=10)
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    print(f"[TERMUX] Polling {args.base_url} every {args.interval}s")
    try:
        while True:
            try:
                msgs = fetch_outbound(args.base_url, args.limit)
                ids = []
                for m in msgs:
                    print(f"[TERMUX] Sending to {m['phone']}: {m['body']}")
                    send_sms(m['phone'], m['body'])
                    ids.append(m['id'])
                if ids:
                    res = mark_sent(args.base_url, ids)
                    print(f"[TERMUX] Marked sent: {res}")
            except Exception as e:
                print(f"[ERR] {e}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[TERMUX] Stopped")

if __name__ == "__main__":
    main()
