#!/usr/bin/env python3
"""
zyxel_callhistory.py

Usage:
  # Use saved body.json for login and download call history
  python zyxel_callhistory.py --body body.json

  # Inline content/key/iv
  python zyxel_callhistory.py --content "BASE64CIPHERTEXT" --key "BASE64KEY" --iv "BASE64IV"

Notes:
- Requires requests:
    pip install requests
- Skips SSL verification by default; use --insecure to allow self-signed certs.
- Session cookies are kept in memory only; nothing is saved to disk.
"""

import argparse
import json
import sys
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Default endpoints
LOGIN_URL = "https://192.168.1.1/UserLogin"
CALLHISTORY_URL = "https://192.168.1.1/cgi-bin/CallHistory?action=Backup"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://192.168.1.1",
    "Referer": "https://192.168.1.1/login",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

def load_body_from_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8").strip()
    try:
        return json.loads(text)
    except Exception as e:
        print("Failed to parse JSON from file:", e)
        sys.exit(1)

def build_post_body(args) -> str:
    if args.content and args.key and args.iv:
        payload = {"content": args.content, "key": args.key, "iv": args.iv}
        return json.dumps(payload, separators=(",", ":"))
    elif args.body:
        obj = load_body_from_file(Path(args.body))
        if not all(k in obj for k in ("content", "key", "iv")):
            print("ERROR: body file does not contain content/key/iv keys.")
            print("File keys:", list(obj.keys()))
            sys.exit(1)
        return json.dumps(obj, separators=(",", ":"))
    else:
        print("No payload provided. Use --body or --content/--key/--iv.")
        sys.exit(1)

def login(session: requests.Session, body_text: str, args) -> None:
    print("Logging in...")
    try:
        resp = session.post(
            LOGIN_URL,
            data=body_text.encode("utf-8"),
            headers=HEADERS,
            verify=not args.insecure,
            timeout=10
        )
    except requests.exceptions.SSLError:
        print("SSL error. Use --insecure for self-signed certs.")
        sys.exit(1)
    except Exception as e:
        print("Login request failed:", e)
        sys.exit(1)

    if resp.status_code == 200:
        print("Login successful, status 200")
    else:
        print("Login failed:", resp.status_code, resp.text)
        sys.exit(1)

def download_callhistory(session: requests.Session) -> None:
    print(f"Downloading call history from {CALLHISTORY_URL} ...")
    r = session.get(CALLHISTORY_URL, stream=True, verify=False)
    if r.status_code == 200:
        filename = "CallHistory.bin"
        cd = r.headers.get("Content-Disposition", "")
        if "filename=" in cd:
            filename = cd.split("filename=")[-1].strip().strip('"')
        outpath = Path(filename)
        with open(outpath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Saved call history to {outpath}")
    else:
        print("Failed to download call history:", r.status_code)
        print("Response headers:", r.headers)

def main():
    p = argparse.ArgumentParser(description="Login to Zyxel router and download call history.")
    p.add_argument("--body", help="Path to JSON file with {content,key,iv}")
    p.add_argument("--content", help="content (base64 ciphertext) to send inline")
    p.add_argument("--key", help="key (base64) to send inline")
    p.add_argument("--iv", help="iv (base64) to send inline")
    p.add_argument("--insecure", action="store_true", help="Skip TLS verification")
    args = p.parse_args()

    session = requests.Session()

    # Build login payload
    body_text = build_post_body(args)
    login(session, body_text, args)

    # Download call history
    download_callhistory(session)

if __name__ == "__main__":
    main()
