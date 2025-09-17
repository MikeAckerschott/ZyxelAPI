#!/usr/bin/env python3
# getCallHistory.py

import requests, urllib3
from http.cookiejar import MozillaCookieJar
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://192.168.1.1"
URL = BASE + "/cgi-bin/CallHistory?action=Backup"
COOKIEFILE = Path("cookies.txt")

def load_session_from_cookies(cookiefile: Path):
    s = requests.Session()
    jar = MozillaCookieJar(str(cookiefile))
    jar.load(ignore_discard=True, ignore_expires=True)
    for c in jar:
        s.cookies.set(c.name, c.value, domain=c.domain or "192.168.1.1", path=c.path or "/")
    return s

def main():
    session = load_session_from_cookies(COOKIEFILE)

    print(f"Downloading {URL} ...")
    r = session.get(URL, stream=True, verify=False)
    print("Status:", r.status_code)

    if r.status_code == 200:
        # try to use filename from Content-Disposition
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
        print("Failed to download. Response headers:", r.headers)

if __name__ == "__main__":
    main()
