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
        try:
            requests.post(url, data={"chat_id": chat_id, "text": message})
        except:
            pass

def get_current_worker_json():
    cf_worker_name = os.getenv('CF_WORKER_NAME')
    cf_account_id = os.getenv('CF_ACCOUNT_ID')
    # Lưu ý: Nếu link worker của bạn không theo cấu trúc này, hãy dán thẳng link vào đây
    url = f"https://{cf_worker_name}.{cf_account_id[:5]}.workers.dev/"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return {"name": "Playlist Live", "items": []}

def update_cloudflare_worker_json(new_link, match_name):
    clean_link = new_link.replace('\\', '').replace('"', '').replace("'", "").strip()
    
    cf_account_id = os.getenv('CF_ACCOUNT_ID')
    cf_worker_name = os.getenv('CF_WORKER_NAME')
    cf_api_token = os.getenv('CF_API_TOKEN')
    
    current_data = get_current_worker_json()
    
    new_item = {
        "title": match_name,
        "group": "LIVE",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B_Sport_2015.png",
        "url": clean_link
    }
    
    current_data["items"].append(new_item)
    json_string = json.dumps(current_data, indent=2, ensure_ascii=False)
    
    worker_script = f"""
export default {{
  async fetch(request, env) {{
    const data = {json_string};
    return new Response(JSON.stringify(data), {{
      headers: {{
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Access-Control-Allow-Origin": "*"
      }}
    }});
  }}
}};"""

    url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/workers/scripts/{cf_worker_name}"
    headers = {
        "Authorization": f"Bearer {cf_api_token}",
        "Content-Type": "application/javascript"
    }

    res = requests.put(url, headers=headers, data=worker_script.encode('utf-8'))
    if res.status_code == 200:
        send_telegram(f"✅ Đã thêm thành công vào Cloudflare!\n⚽ {match_name}")
    else:
        send_telegram(f"❌ Lỗi Cloudflare: {res.status_code}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    if not target_url: return

    # FIX TẠI ĐÂY: Đổi update_gist thành update_cloudflare_worker_json
    if ".m3u8" in target_url.lower():
        update_cloudflare_worker_json(target_url, match_name)
        return

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    link = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(target_url)
        
        for i in range(30):
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log = json.loads(entry['message'])['message']
                    if 'params' in log and 'request' in log['params']:
                        u = log['params']['request']['url']
                        if ".m3u8" in u.lower():
                            blacklist = ["cloudflarestream.com", "manifest/video.m3u8", "doubleclick"]
                            if any(word in u.lower() for word in blacklist):
                                continue
                            link = u
                            break
                except: continue
            if link: break
            time.sleep(1)
        driver.quit()
    except Exception as e:
        print(f"Lỗi Selenium: {e}")

    if not link:
        cmd = ['yt-dlp', '-g', '--referer', target_url, target_url]
        res = subprocess.run(cmd, capture_output=True, text=True)
        link = res.stdout.strip()

    if link and "http" in link:
        # FIX TẠI ĐÂY: Đổi update_gist thành update_cloudflare_worker_json
        update_cloudflare_worker_json(link, match_name)
    else:
        send_telegram(f"❌ Bế tắc với {match_name}.")

if __name__ == "__main__":
    get_link()
