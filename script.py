import os
import subprocess
import requests
import re
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def send_telegram(message):
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try: requests.post(url, data={"chat_id": chat_id, "text": message})
        except: pass

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
    clean_link = new_link.replace('\\', '').replace('"', '').replace("'", "").strip()
    gist_id = os.getenv('GIST_ID')
    gist_token = os.getenv('GIST_TOKEN')
    current_content = get_current_gist_content(gist_id, gist_token)
    if not current_content.strip(): current_content = '#EXTM3U'

    new_entry = f'\n#EXTINF:-1 group-title="LIVE", {match_name}\n{clean_link}'
    updated_content = current_content.strip() + new_entry

    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    res_get = requests.get(url, headers=headers).json()
    first_file = list(res_get['files'].keys())[0]
    data = {"files": {first_file: {"content": updated_content}}}
    res = requests.patch(url, headers=headers, json=data)
    if res.status_code == 200:
        send_telegram(f"✅ Thành công: {match_name}\n🔗 {clean_link}")
    else:
        send_telegram(f"❌ Lỗi Gist: {res.status_code}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    if not target_url: return

    link = None
    print(f"📡 Đang dùng Chrome ảo quét Network cho: {target_url}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Kích hoạt tính năng bắt log mạng
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(target_url)
        
        # Đợi trang load và bắt các request ngầm trong 20 giây
        for _ in range(20):
            logs = driver.get_log('performance')
            for entry in logs:
                log = json.loads(entry['message'])['message']
                if 'Network.requestWillBeSent' in log['method']:
                    request_url = log['params']['request']['url']
                    if ".m3u8" in request_url and "apple" not in request_url and "schema" not in request_url:
                        link = request_url
                        break
            if link: break
            time.sleep(1)
        driver.quit()
    except Exception as e:
        print(f"Lỗi: {e}")

    # Dự phòng bằng yt-dlp nếu Network Sniffing thất bại
    if not link:
        cmd = ['yt-dlp', '-g', '--referer', target_url, target_url]
        res = subprocess.run(cmd, capture_output=True, text=True)
        link = res.stdout.strip()

    if link and "http" in link:
        update_gist(link, match_name)
    else:
        send_telegram(f"❌ Vẫn không lấy được link cho {match_name}. Luongson đang chặn IP máy chủ GitHub.")

if __name__ == "__main__":
    get_link()
