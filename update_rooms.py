import os
import re
import requests
from bs4 import BeautifulSoup

html_path = "index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "html.parser")
headers = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
has_changed = False

# 1. 巡邏招待所 (>=4人)
for link in soup.find_all("a", attrs={"data-room": True}):
    room_id = link["data-room"]
    try:
        res = session.get(link["href"], headers=headers, timeout=10)
        if res.status_code == 200:
            match = re.search(r'"memberCount"\s*:\s*(\d+)', res.text)
            if match and int(match.group(1)) >= 4:
                if "busy" not in link.get("class", []):
                    link["class"] = link.get("class", []) + ["busy"]
                    has_changed = True
            elif "busy" in link.get("class", []):
                link["class"].remove("busy")
                has_changed = True
    except: pass

# 2. 巡邏對談室 (>=1人)
for link in soup.find_all("a", attrs={"data-talk": True}):
    talk_id = link["data-talk"]
    try:
        res = session.get(link["href"], headers=headers, timeout=10)
        if res.status_code == 200:
            match = re.search(r'"memberCount"\s*:\s*(\d+)', res.text)
            if match and int(match.group(1)) >= 1:
                if "busy" not in link.get("class", []):
                    link["class"] = link.get("class", []) + ["busy"]
                    has_changed = True
            elif "busy" in link.get("class", []):
                link["class"].remove("busy")
                has_changed = True
    except: pass

if has_changed:
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))
