#!/usr/bin/env python3
"""
router_login.py

Usage examples:
  # Replay using saved body.json (default)
  python router_login.py --body body.json

  # Inline (pass content/key/iv from HAR)
  python router_login.py --content "BASE64CIPHERTEXT" --key "BASE64KEY" --iv "BASE64IV"

  # Save cookies and reuse
  python router_login.py --body body.json --cookies cookies.txt

Notes:
- This script does NOT implement the client-side encryption routine that produces content/key/iv.
  To automate logins long-term you will need to re-implement the router's JS encryption in Python,
  or use a headless browser to run the page JS and obtain the payload dynamically.
"""

import argparse
import json
import sys
from pathlib import Path

import requests
from http.cookiejar import MozillaCookieJar

DEFAULT_URL = "https://192.168.1.1/UserLogin"
DEFAULT_COOKIES = "cookies.txt"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://192.168.1.1",
    "Referer": "https://192.168.1.1/login",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

def load_body_from_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8").strip()
    # The HAR shows the client posted a JSON string as form-encoded body (browser used application/x-www-form-urlencoded)
    # The simplest way is to send the JSON string as the request body unchanged.
    # If file already contains a JSON object, load it and re-dump compactly.
    try:
        parsed = json.loads(text)
        # dump compact single-line representation (same as postData.text in HAR)
        return parsed
    except Exception:
        # file may already be the exact JSON text expected; try to parse as string value
        try:
            # If file contains something like: {"content":"...","key":"...","iv":"..."}
            parsed = json.loads(text)
            return parsed
        except Exception as e:
            print("Failed to parse JSON from file:", e)
            sys.exit(1)

def save_cookies_cookiejar(session: requests.Session, path: Path):
    jar = MozillaCookieJar(str(path))
    for c in session.cookies:
        jar.set_cookie(requests.cookies.create_cookie(name=c.name, value=c.value, domain=c.domain, path=c.path))
    jar.save(ignore_discard=True, ignore_expires=True)

def load_cookies_cookiejar(session: requests.Session, path: Path):
    jar = MozillaCookieJar(str(path))
    try:
        jar.load(ignore_discard=True, ignore_expires=True)
    except FileNotFoundError:
        return
    for c in jar:
        # convert back to requests cookie
        session.cookies.set(name=c.name, value=c.value, domain=c.domain, path=c.path)

def build_post_body(args) -> str:
    """
    Return a JSON string to send as the body.
    The HAR sent the JSON object as the POST body with content-type application/x-www-form-urlencoded.
    We'll send the compact JSON string as the body (requests will not re-encode it).
    """
    if args.content and args.key and args.iv:
        payload = {"content": args.content, "key": args.key, "iv": args.iv}
        return json.dumps(payload, separators=(",", ":"))
    elif args.body:
        obj = load_body_from_file(Path(args.body))
        # Ensure it's a dict with content/key/iv
        if not all(k in obj for k in ("content", "key", "iv")):
            print("ERROR: body file does not contain content/key/iv keys.")
            print("File parsed content keys:", list(obj.keys()))
            sys.exit(1)
        return json.dumps(obj, separators=(",", ":"))
    else:
        print("No payload provided. Use --body or --content/--key/--iv.")
        sys.exit(1)

def main():
    p = argparse.ArgumentParser(description="Send /UserLogin POST to Zyxel router using an existing content/key/iv blob.")
    p.add_argument("--url", default=DEFAULT_URL, help=f"Login URL (default: {DEFAULT_URL})")
    p.add_argument("--body", help="Path to JSON file with {content,key,iv}")
    p.add_argument("--content", help="content (base64 ciphertext) to send inline")
    p.add_argument("--key", help="key (base64) to send inline")
    p.add_argument("--iv", help="iv (base64) to send inline")
    p.add_argument("--cookies", default=DEFAULT_COOKIES, help=f"Cookie file to save/load (default: {DEFAULT_COOKIES})")
    p.add_argument("--insecure", action="store_true", help="Skip TLS verification (useful for router self-signed certs)")
    p.add_argument("--show-headers", action="store_true", help="Print response headers")
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    args = p.parse_args()

    # Build payload
    body_text = build_post_body(args)

    s = requests.Session()
    # Try to load existing cookies if present
    cookie_path = Path(args.cookies)
    if cookie_path.exists():
        try:
            load_cookies_cookiejar(s, cookie_path)
            if args.verbose:
                print(f"Loaded cookies from {cookie_path}")
        except Exception as e:
            if args.verbose:
                print("Failed to load cookies:", e)

    # Send request
    try:
        resp = s.post(args.url,
                      data=body_text.encode("utf-8"),
                      headers=HEADERS,
                      verify=not args.insecure,
                      timeout=10)
    except requests.exceptions.SSLError as e:
        print("SSL error. Try --insecure to disable verification.")
        raise SystemExit(1)
    except Exception as e:
        print("Request failed:", e)
        raise SystemExit(1)

    # Show response
    if args.show_headers or args.verbose:
        print("=== Response headers ===")
        for k, v in resp.headers.items():
            print(f"{k}: {v}")
        print("========================\n")

    print("Status:", resp.status_code, resp.reason)
    print("Response body:")
    print(resp.text)

    # Save cookies
    try:
        save_cookies_cookiejar(s, cookie_path)
        if args.verbose:
            print(f"Saved cookies to {cookie_path}")
    except Exception as e:
        if args.verbose:
            print("Failed to save cookies:", e)

    # Helpful note: the router returns a JSON body that itself contains encrypted JSON in 'content' and 'iv'.
    # You may need to decrypt it using the same routine as the page JS if you want human-readable response.

if __name__ == "__main__":
    main()
