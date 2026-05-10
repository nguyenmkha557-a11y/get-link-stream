import os
import subprocess
import requests
import re

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
    # DỌN DẸP LINK: Xóa sạch dấu gạch chéo ngược \ và khoảng trắng thừa
    clean_link = new_link.replace('\\', '').strip()
    
    gist_id = os.getenv('GIST_ID')
    gist_token = os.getenv('GIST_TOKEN')
    current_content = get_current_gist_content(gist_id, gist_token)
    
    if not current_content.strip():
        current_content = '#EXTM3U'

    new_entry = f'\n#EXTINF:-1 group-title="THỂ THAO" tvg-logo="https://e0.365dm.com/24/01/2048x1152/skysports-sky-sports-tennis_6437040.jpg", {match_name}\n{clean_link}'
    updated_content = current_content.strip() + new_entry

    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    res_get = requests.get(url, headers=headers).json()
    first_file = list(res_get['files'].keys())[0]
    
    data = {"files": {first_file: {"content": updated_content}}}
    res = requests.patch(url, headers=headers, json=data)
    if res.status_code == 200:
        send_telegram(f"✅ Đã thêm: {match_name}\n🔗 {clean_link}")
    else:
        send_telegram(f"❌ Lỗi Gist: {res.status_code}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    if not target_url: return

    # Nếu người dùng gửi thẳng link .m3u8, lấy luôn không cần bẻ khóa
    if ".m3u8" in target_url.lower() and "http" in target_url.lower():
        update_gist(target_url, match_name)
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": target_url
    }

    link = None
    # Thử yt-dlp trước
    cmd = ['yt-dlp', '-g', '--referer', target_url, target_url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    link = result.stdout.strip()

    # Nếu yt-dlp không ra, quét thủ công
    if not link or "http" not in link:
        try:
            response = requests.get(target_url, headers=headers, timeout=15)
            # Quét tất cả link m3u8
            found = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', response.text)
            if found:
                link = found[0]
        except: pass

    if link and "http" in link:
        update_gist(link, match_name)
    else:
        send_telegram(f"❌ Không tìm thấy link stream cho: {match_name}")

if __name__ == "__main__":
    get_link()
