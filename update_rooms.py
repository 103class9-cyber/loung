import os
import re
import requests
from bs4 import BeautifulSoup

html_path = "index.html"
if not os.path.exists(html_path):
    print("❌ 錯誤：找不到 index.html 檔案")
    exit(1)

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "html.parser")
room_links = soup.find_all("a", attrs={"data-room": True})

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

has_changed = False
print("🚀 開始掃描 LINE 招待所房間即時人數...")

for link in room_links:
    room_id = link["data-room"]
    line_url = link["href"]
    
    try:
        response = requests.get(line_url, headers=headers, timeout=15)
        if response.status_code == 200:
            member_match = re.search(r"成員\s*[:：]?\s*([\d,]+)", response.text)
            if member_match:
                current_members = int(member_match.group(1).replace(",", ""))
                print(f"房號 {room_id} ｜ 當前人數：{current_members} 人")
                
                current_classes = link.get("class", [])
                
                # 🔥 核心判定優化：當人數大於等於 4 人時，才觸發滿房鎖定
                if current_members >= 4:
                    if "busy" not in current_classes:
                        current_classes.append("busy")
                        link["class"] = current_classes
                        has_changed = True
                        print(f" ➔ 🔴 房間 {room_id} 達到或超過4人，自動標記為【使用中】")
                else:
                    # 如果人數低於 4 人，自動解鎖房間恢復空房
                    if "busy" in current_classes:
                        current_classes.remove("busy")
                        link["class"] = current_classes if current_classes else None
                        has_changed = True
                        print(f" ➔ 🟢 房間 {room_id} 釋出空位，網頁已恢復空房")
            else:
                print(f"⚠️ 房號 {room_id} ｜ 無法解析 LINE 人數（可能格式改變）")
        else:
            print(f"❌ 房號 {room_id} ｜ 請求失敗，狀態碼：{response.status_code}")
    except Exception as e:
        print(f"💥 房號 {room_id} ｜ 連線異常：{e}")

if has_changed:
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print("✅ 網頁狀態有變更，index.html 檔案已成功更新寫入。")
else:
    print("☕ 掃描完畢：所有人數狀態均無變更，跳過本次寫入。")
