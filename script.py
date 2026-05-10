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

def update_gist(new_link, match_name):
    clean_link = new_link.replace('\\', '').replace('"', '').replace("'", "").strip()
    gist_id = os.getenv('GIST_ID')
    gist_token = os.getenv('GIST_TOKEN')
    
    # Lấy tên file và nội dung cũ
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    res_get = requests.get(url, headers=headers).json()
    first_file = list(res_get['files'].keys())[0]
    current_content = res_get['files'][first_file]['content']
    
    if not current_content.strip(): current_content = '#EXTM3U'
    new_entry = f'\n#EXTINF:-1 group-title="LIVE", {match_name}\n{clean_link}'
    updated_content = current_content.strip() + new_entry

    data = {"files": {first_file: {"content": updated_content}}}
    requests.patch(url, headers=headers, json=data)
    send_telegram(f"✅ GitHub đã thử và thành công!\n⚽ {match_name}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    if not target_url: return

    chrome_options = Options()
    chrome_options.add_argument("--headless") # GitHub bắt buộc phải chạy ngầm
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    link = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(target_url)
        
        # GitHub không có người bấm Play, nên mình hy vọng video tự chạy
        for i in range(30):
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log = json.loads(entry['message'])['message']
                    if 'params' in log and 'request' in log['params']:
                        url = log['params']['request']['url']
                        if ".m3u8" in url and "apple" not in url and "schema" not in url:
                            link = url
                            break
                except: continue
            if link: break
            time.sleep(1)
        driver.quit()
    except Exception as e:
        print(f"Lỗi: {e}")

    if link:
        update_gist(link, match_name)
    else:
        send_telegram(f"❌ GitHub bó tay với {match_name} (Có thể do chặn IP).")

if __name__ == "__main__":
    get_link()
