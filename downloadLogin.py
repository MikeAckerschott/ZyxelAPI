import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

base_url = "http://192.168.1.1/login"
session = requests.Session()

# Download main HTML
resp = session.get(base_url)
html = resp.text

with open("login.html", "w", encoding="utf-8") as f:
    f.write(html)

soup = BeautifulSoup(html, "html.parser")

# Collect all links to assets
assets = []
for tag in soup.find_all(["link", "script", "img"]):
    url = tag.get("href") or tag.get("src")
    if url:
        assets.append(url)

# Download assets
for asset in assets:
    full_url = urljoin(base_url, asset)
    path = asset.lstrip("./").replace("/", os.sep)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    print("Downloading:", full_url)
    r = session.get(full_url)
    with open(path, "wb") as f:
        f.write(r.content)
