import os
import re
import requests
from bs4 import BeautifulSoup

# ==========================================
# ⚙️ 設定區
# ==========================================
REPO_OWNER = "103class9-cyber"
REPO_NAME = "loung"
# ==========================================

html_path = "index.html"
if not os.path.exists(html_path):
    print("❌ 錯誤：找不到 index.html 檔案")
    exit(1)

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "html.parser")
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
has_changed = False
total_busy_count = 0

# -------------------------------------------------------------
# 1. 巡邏 VIP 招待所房間 (門檻：大於等於 4 人客滿)
# -------------------------------------------------------------
print("🚀 [1/3] 開始巡邏 VIP 招待所房間人數...")
room_links = soup.find_all("a", attrs={"data-room": True})

for link in room_links:
    room_id = link["data-room"]
    line_url = link["href"]
    try:
        response = requests.get(line_url, headers=headers, timeout=15)
        if response.status_code == 200:
            member_match = re.search(r'"memberCount"\s*:\s*(\d+)', response.text)
            if not member_match:
                member_match = re.search(r"成員\s*[:：]?\s*([\d,]+)", response.text)
            
            if member_match:
                current_members = int(member_match.group(1).replace(",", ""))
                current_classes = link.get("class", [])
                
                if current_members >= 4:
                    total_busy_count += 1
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
        print(f"💥 房號 {room_id} 連線異常: {e}")

# -------------------------------------------------------------
# 2. 巡邏 Live Chat 線上對談室 (門檻：大於等於 1 人即使用中)
# -------------------------------------------------------------
print("\n🔮 [2/3] 開始巡邏 Live Chat 尊榮線上對談人數...")
talk_links = soup.find_all("a", attrs={"data-talk": True})

for link in talk_links:
    talk_id = link["data-talk"]
    line_url = link["href"]
    if "/R/meeting/" in line_url:
        continue
    try:
        response = requests.get(line_url, headers=headers, timeout=15)
        if response.status_code == 200:
            member_match = re.search(r"成員\s*[:：]?\s*([\d,]+)", response.text)
            if member_match:
                current_members = int(member_match.group(1).replace(",", ""))
                current_classes = link.get("class", [])
                if current_members >= 1:
                    total_busy_count += 1
                    if "busy" not in current_classes:
                        current_classes.append("busy")
                        link["class"] = current_classes
                        has_changed = True
                        print(f" ➔ 🔴 對談室 {talk_id} 有人進駐 (>=1人)，自動亮起【使用中】")
                else:
                    if "busy" in current_classes:
                        current_classes.remove("busy")
                        link["class"] = current_classes if current_classes else None
                        has_changed = True
                        print(f" ➔ 🟢 對談室 {talk_id} 釋出空閒")
        except Exception as e:
            print(f"💥 對談室 {talk_id} 連線異常: {e}")

# -------------------------------------------------------------
# 3. 智慧同步：計算「時光交換中」計數器
# -------------------------------------------------------------
counter_span = soup.find("span", class_="counter-num")
if counter_span and counter_span.string != str(total_busy_count):
    counter_span.string = str(total_busy_count)
    has_changed = True
    print(f"\n📊 [3/3] 計數器更新：當前在線爆滿組數為 {total_busy_count} 組。")

# -------------------------------------------------------------
# 4. 智慧同步：抓取 GitHub Issues 全自動更新網頁公告欄
# -------------------------------------------------------------
print("\n📝 開始撈取 GitHub Issues 同步公告條文...")
issues_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues?state=open"
try:
    res = requests.get(issues_url, timeout=10)
    if res.status_code == 200:
        issues_list = res.json()
        notice_container = soup.find(id="auto-notices")
        if notice_container and issues_list:
            new_html = ""
            for idx, issue in enumerate(issues_list):
                active_class = "active" if idx == 0 else ""
                title = issue["title"]
                body_text = issue["body"].replace("\n", "<br>") if issue["body"] else ""
                new_html += f"""
                <div id="sub-panel-issue-{idx}" class="sub-tab-panel {active_class}">
                    <div class="card-box sub-notice-box">
                        <div class="policy-list">
                            <div class="policy-item notice-cyan">
                                <div class="policy-item-title">🔔 {title}</div>
                                <div class="policy-item-desc">{body_text}</div>
                            </div>
                        </div>
                    </div>
                </div>
                """
            notice_container.clear()
            notice_container.append(BeautifulSoup(new_html, "html.parser"))
            has_changed = True
            print("✅ 成功：最新公告文字已順利與 GitHub Issues 同步！")
except Exception as e:
    print(f"⚠️ 公告同步失敗（保持預設公告）：{e}")

# -------------------------------------------------------------
# 5. 寫入儲存
# -------------------------------------------------------------
if has_changed:
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print("\n🎉 旗艦自動化作業完成：代碼已推回 index.html！")
else:
    print("\n☕ 掃描完成：無任何狀態變更。")
