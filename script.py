import os
import subprocess
import requests
import re
import base64

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
    # Dọn dẹp link sạch sẽ nhất có thể
    clean_link = new_link.replace('\\', '').replace('"', '').replace("'", "").strip()
    
    gist_id = os.getenv('GIST_ID')
    gist_token = os.getenv('GIST_TOKEN')
    current_content = get_current_gist_content(gist_id, gist_token)
    
    if not current_content.strip():
        current_content = '#EXTM3U'

    new_entry = f'\n#EXTINF:-1 group-title="LIVE" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B_Sport_2015.png", {match_name}\n{clean_link}'
    updated_content = current_content.strip() + new_entry

    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    res_get = requests.get(url, headers=headers).json()
    first_file = list(res_get['files'].keys())[0]
    
    data = {"files": {first_file: {"content": updated_content}}}
    res = requests.patch(url, headers=headers, json=data)
    if res.status_code == 200:
        send_telegram(f"✅ Đã thêm thành công!\n⚽ {match_name}")
    else:
        send_telegram(f"❌ Lỗi Gist: {res.status_code}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    if not target_url: return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": target_url
    }

    link = None

    try:
        # Bước 1: Tải mã nguồn trang chính
        response = requests.get(target_url, headers=headers, timeout=15)
        html = response.text

        # Bước 2: Tìm link m3u8 trực tiếp bằng Regex
        found = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', html)
        
        # Bước 3: Nếu không có, tìm các link Iframe Embed
        if not found:
            print("Đang tìm Iframe ẩn...")
            iframes = re.findall(r'iframe.*?src=["\'](https?://[^"\']+)["\']', html, re.IGNORECASE)
            for frame_url in iframes:
                if "facebook" in frame_url or "google" in frame_url: continue
                try:
                    f_res = requests.get(frame_url, headers={"User-Agent": headers["User-Agent"], "Referer": target_url}, timeout=10)
                    found += re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', f_res.text)
                except: continue

        # Bước 4: Lọc lấy link thật
        if found:
            for l in found:
                l = l.replace('\\/', '/')
                if "m3u8" in l and "apple.com" not in l and "schema.org" not in l:
                    link = l
                    break

        # Bước 5: Nếu vẫn không được, dùng yt-dlp làm cứu cánh cuối
        if not link:
            cmd = ['yt-dlp', '-g', '--referer', target_url, target_url]
            res = subprocess.run(cmd, capture_output=True, text=True)
            link = res.stdout.strip()

    except Exception as e:
        print(f"Lỗi: {e}")

    if link and "http" in link:
        update_gist(link, match_name)
    else:
        send_telegram(f"❌ Bế tắc: Luongson bảo mật quá kỹ hoặc chưa có luồng phát cho {match_name}")

if __name__ == "__main__":
    get_link()
