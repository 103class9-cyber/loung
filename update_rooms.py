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
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}
has_changed = False

# -------------------------------------------------------------
# 1. 巡邏 VIP 招待所房間 (門檻：大於等於 4 人客滿)
# -------------------------------------------------------------
print("🚀 開始巡邏 VIP 招待所房間人數...")
room_links = soup.find_all("a", attrs={"data-room": True})

for link in room_links:
    room_id = link["data-room"]
    line_url = link["href"]
    
    try:
        response = requests.get(line_url, headers=headers, timeout=15)
        if response.status_code == 200:
            # 💡 雙重保險高階匹配：優先尋找 LINE 最穩定的 og:description 結構
            member_match = re.search(r'content="[^"]*成員\s*[:：]\s*([\d,]+)\s*人', response.text)
            if not member_match:
                member_match = re.search(r"成員\s*[:：]?\s*([\d,]+)\s*人", response.text)
            if not member_match:
                member_match = re.search(r"成員\s*[:：]?\s*([\d,]+)", response.text)
            if not member_match:
                # 備用防護：抓取 LINE 系統腳本中的 JSON 序列化人數資料
                member_match = re.search(r'"memberCount"\s*:\s*(\d+)', response.text)

            if member_match:
                current_members = int(member_match.group(1).replace(",", ""))
                print(f"房號 {room_id} ｜ 實際在線人數：{current_members} 人")
                
                current_classes = link.get("class", [])
                if current_members >= 4:
                    if "busy" not in current_classes:
                        current_classes.append("busy")
                        link["class"] = current_classes
                        has_changed = True
                        print(f" ➔ 🔴 房間 {room_id} 達到客滿線 (>=4人)，自動亮起【使用中】")
                else:
                    if "busy" in current_classes:
                        current_classes.remove("busy")
                        link["class"] = current_classes if current_classes else None
                        has_changed = True
                        print(f" ➔ 🟢 房間 {room_id} 尚有空位 (<4人)，自動釋出房間")
            else:
                print(f"⚠️ 房號 {room_id} ｜ 無法成功解析人數文字結構")
        else:
            print(f"❌ 房號 {room_id} ｜ 請求失敗，狀態碼：{response.status_code}")
    except Exception as e:
        print(f"💥 房號 {room_id} ｜ 連線異常：{e}")

# -------------------------------------------------------------
# 2. 巡邏 Live Chat 尊榮線上對談室 (門檻：大於等於 1 人即使用中)
# -------------------------------------------------------------
print("\n🔮 開始巡邏 Live Chat 尊榮線上對談人數...")
talk_links = soup.find_all("a", attrs={"data-talk": True})

for link in talk_links:
    talk_id = link["data-talk"]
    line_url = link["href"]
    
    # 💡 如果使用的是私密會議室連結，提示所長並維持現有狀態不誤刪
    if "/R/meeting/" in line_url:
        print(f"💡 對談室 {talk_id} ｜ 偵測為私密 LINE 會議室，官方預設不公開人數，維持獨立防線。")
        continue

    try:
        response = requests.get(line_url, headers=headers, timeout=15)
        if response.status_code == 200:
            member_match = re.search(r'content="[^"]*成員\s*[:：]\s*([\d,]+)\s*人', response.text)
            if not member_match:
                member_match = re.search(r"成員\s*[:：]?\s*([\d,]+)", response.text)
            
            if member_match:
                current_members = int(member_match.group(1).replace(",", ""))
                print(f"對談室 {talk_id} ｜ 當前人數：{current_members} 人")
                
                current_classes = link.get("class", [])
                if current_members >= 1:
                    if "busy" not in current_classes:
                        current_classes.append("busy")
                        link["class"] = current_classes
                        has_changed = True
                        print(f" ➔ 🔴 对談室 {talk_id} 有人進駐 (>=1人)，自動亮起【使用中】")
                else:
                    if "busy" in current_classes:
                        current_classes.remove("busy")
                        link["class"] = current_classes if current_classes else None
                        has_changed = True
                        print(f" ➔ 🟢 對談室 {talk_id} 釋出空閒")
    except Exception as e:
        print(f"💥 對談室 {talk_id} ｜ 連線異常：{e}")

# -------------------------------------------------------------
# 3. 儲存與寫入檔案
# -------------------------------------------------------------
if has_changed:
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print("\n✅ 檢測到變更，網頁代碼已自動更新寫入！")
else:
    print("\n☕ 掃描完畢：無任何狀態變更，安全跳過。")
