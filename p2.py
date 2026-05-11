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

def get_current_worker_content():
    """Lấy nội dung M3U hiện tại từ Cloudflare Worker"""
    worker_name = os.getenv('CF_WORKER_NAME')
    # Link mặc định của worker, bạn có thể sửa subdomain nếu cần
    url = f"https://{worker_name}.nguyenmanhcuong83ro.workers.dev/"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200 and "#EXTM3U" in res.text:
            return res.text.strip()
    except:
        pass
    return '#EXTM3U url-tvg="https://vnepg.site/epg.xml"'

def update_cloudflare_worker(new_link, match_name):
    """Ghi đè mã nguồn Cloudflare Worker với nội dung M3U mới"""
    clean_link = new_link.replace('\\', '').replace('"', '').replace("'", "").strip()
    
    cf_account_id = os.getenv('CF_ACCOUNT_ID')
    cf_worker_name = os.getenv('CF_WORKER_NAME')
    cf_api_token = os.getenv('CF_API_TOKEN')

    # 1. Lấy dữ liệu cũ và nối thêm link mới
    current_content = get_current_worker_content()
    new_entry = f'\n#EXTINF:-1 group-title="LIVE" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B_Sport_2015.png", {match_name}\n{clean_link}'
    updated_m3u = current_content + new_entry

    # 2. Tạo mã nguồn JS (Định dạng Service Worker để tránh lỗi 'export')
    worker_script = f'''
addEventListener("fetch", event => {{
  event.respondWith(handleRequest(event.request))
}});

async function handleRequest(request) {{
  const m3u = `{updated_m3u}`;
  return new Response(m3u, {{
    headers: {{
      "Content-Type": "application/x-mpegurl; charset=utf-8",
      "Cache-Control": "no-store, no-cache, must-revalidate",
      "Access-Control-Allow-Origin": "*"
    }}
  }});
}}'''

    # 3. Gửi PUT request tới Cloudflare API
    url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/workers/scripts/{cf_worker_name}"
    headers = {
        "Authorization": f"Bearer {cf_api_token}",
        "Content-Type": "application/javascript"
    }

    res = requests.put(url, headers=headers, data=worker_script.encode('utf-8'))
    
    if res.status_code == 200:
        send_telegram(f"✅ Cloudflare Updated!\n⚽ {match_name}\n🔗 {clean_link}")
    else:
        send_telegram(f"❌ Lỗi Cloudflare: {res.status_code}\n{res.text[:100]}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    if not target_url: return

    # Nếu người dùng gửi thẳng link m3u8
    if ".m3u8" in target_url.lower():
        update_cloudflare_worker(target_url, match_name)
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
                        url = log['params']['request']['url']
                        
                        if ".m3u8" in url.lower():
                            blacklist = ["cloudflarestream.com", "manifest/video.m3u8", "doubleclick", "schema.org", "apple.com"]
                            if any(word in url.lower() for word in blacklist):
                                continue
                            
                            whitelist = ["live", "index.m3u8", "blv", "pull", "stream"]
                            if any(word in url.lower() for word in whitelist):
                                link = url
                                break
                except:
                    continue
            if link: break
            time.sleep(1)
        driver.quit()
    except Exception as e:
        print(f"Lỗi Selenium: {e}")

    # Dự phòng bằng yt-dlp
    if not link:
        cmd = ['yt-dlp', '-g', '--referer', target_url, target_url]
        res = subprocess.run(cmd, capture_output=True, text=True)
        link = res.stdout.strip()

    if link and "http" in link:
        update_cloudflare_worker(link, match_name)
    else:
        send_telegram(f"❌ Bế tắc với {match_name}. Không tìm thấy luồng live hợp lệ.")

if __name__ == "__main__":
    get_link()
