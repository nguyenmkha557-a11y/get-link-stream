import os
import subprocess
import requests
import re
import time

def send_telegram(message):
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message})

def get_current_gist_content(gist_id, gist_token):
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            files = res.json().get('files', {})
            first_file = list(files.keys())[0]
            return files[first_file].get('content', '')
    except: pass
    return ""

def update_gist(new_link, match_name):
    gist_id = os.getenv('GIST_ID')
    gist_token = os.getenv('GIST_TOKEN')
    current_content = get_current_gist_content(gist_id, gist_token)
    if not current_content.strip():
        current_content = '#EXTM3U'

    # Tạo dòng chèn mới
    new_entry = f'\n#EXTINF:-1 group-title="THỂ THAO" tvg-logo="https://e0.365dm.com/24/01/2048x1152/skysports-sky-sports-tennis_6437040.jpg", {match_name}\n{new_link}'
    updated_content = current_content.strip() + new_entry

    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    res_get = requests.get(url, headers=headers).json()
    first_file = list(res_get['files'].keys())[0]
    
    data = {"files": {first_file: {"content": updated_content}}}
    res = requests.patch(url, headers=headers, json=data)
    if res.status_code == 200:
        send_telegram(f"✅ Đã thêm: {match_name}")
    else:
        send_telegram(f"❌ Lỗi Gist: {res.status_code}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    if not target_url: return

    # Giả lập Header như trình duyệt thật
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://quechoa10.live/",
        "Origin": "https://quechoa10.live"
    }

    print(f"🚀 Đang soi F12 giả lập cho: {match_name}")
    
    # Bước 1: Thử yt-dlp trước (Dành cho Buncha và các trang dễ)
    cmd = ['yt-dlp', '-g', '--referer', target_url, target_url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    link = result.stdout.strip()

    # Bước 2: Nếu thất bại, bắt đầu soi mã nguồn sâu (Dành cho Quechoa)
    if not link or "http" not in link:
        try:
            session = requests.Session()
            response = session.get(target_url, headers=headers, timeout=15)
            html = response.text

            # Tìm link m3u8 trong các biến JavaScript (Thường nằm trong player setup)
            # Regex này tìm tất cả link kết thúc bằng m3u8 hoặc các link stream ẩn
            patterns = [
                r'["\'](https?://[^\s\'"]+\.m3u8[^\s\'"]*)["\']',
                r'file:\s*["\'](https?://[^"\']+)["\']',
                r'source:\s*["\'](https?://[^"\']+)["\']'
            ]
            
            potential_links = []
            for p in patterns:
                found = re.findall(p, html)
                potential_links.extend(found)

            # Lọc link rác
            for l in potential_links:
                l = l.replace('\\/', '/')
                if "m3u8" in l and "schema.org" not in l and "apple.com" not in l:
                    link = l
                    break
        except Exception as e:
            print(f"Lỗi soi nguồn: {e}")

    if link and "http" in link:
        update_gist(link, match_name)
    else:
        send_telegram(f"❌ Vẫn không bẻ được {match_name}. Có lẽ trang này dùng link động rồi đại ca!")

if __name__ == "__main__":
    get_link()
