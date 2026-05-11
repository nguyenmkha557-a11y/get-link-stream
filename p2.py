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
    """Lấy dữ liệu JSON hiện tại từ Worker"""
    cf_worker_name = os.getenv('CF_WORKER_NAME')
    cf_account_id = os.getenv('CF_ACCOUNT_ID')
    url = f"https://{cf_worker_name}.{cf_account_id[:5]}.workers.dev/"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json() # Trả về dictionary
    except:
        pass
    # Nếu chưa có gì, trả về cấu trúc khung chuẩn
    return {"name": "Playlist Live", "items": []}

def update_cloudflare_worker_json(new_link, match_name):
    clean_link = new_link.replace('\\', '').replace('"', '').replace("'", "").strip()
    
    cf_account_id = os.getenv('CF_ACCOUNT_ID')
    cf_worker_name = os.getenv('CF_WORKER_NAME')
    cf_api_token = os.getenv('CF_API_TOKEN')
    
    # 1. Lấy dữ liệu cũ (dạng Dict) và thêm item mới
    current_data = get_current_worker_json()
    
    new_item = {
        "title": match_name,
        "group": "LIVE",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B_Sport_2015.png",
        "url": clean_link
    }
    
    # Thêm vào danh sách items
    current_data["items"].append(new_item)
    
    # 2. Tạo mã nguồn Worker trả về JSON
    # Dùng json.dumps để biến dictionary thành chuỗi JSON chuẩn
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

    # 3. Gửi lên Cloudflare API
    url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/workers/scripts/{cf_worker_name}"
    headers = {
        "Authorization": f"Bearer {cf_api_token}",
        "Content-Type": "application/javascript"
    }

    res = requests.put(url, headers=headers, data=worker_script.encode('utf-8'))
    if res.status_code == 200:
        send_telegram(f"✅ Đã thêm thành công!\n⚽ {match_name}\n🔗 {clean_link}")
    else:
        send_telegram(f"❌ Lỗi Gist: {res.status_code}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    if not target_url: return

    # Nếu người dùng gửi thẳng link m3u8
    if ".m3u8" in target_url.lower():
        update_gist(target_url, match_name)
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
        
        # Quét log mạng liên tục để tìm link xịn
        for i in range(30):
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log = json.loads(entry['message'])['message']
                    if 'params' in log and 'request' in log['params']:
                        url = log['params']['request']['url']
                        
                        # ĐIỀU KIỆN LỌC THÔNG MINH
                        if ".m3u8" in url.lower():
                            # 1. BỘ LỌC CHẶN (Loại bỏ quảng cáo Cloudflare và rác)
                            blacklist = ["cloudflarestream.com", "manifest/video.m3u8", "doubleclick", "schema.org", "apple.com"]
                            if any(word in url.lower() for word in blacklist):
                                continue
                            
                            # 2. BỘ LỌC ƯU TIÊN (Nhận diện link stream xịn)
                            whitelist = ["live", "index.m3u8", "blv", "pull", "stream"]
                            if any(word in url.lower() for word in whitelist):
                                link = url
                                break # Đã tìm thấy link chuẩn, thoát ngay
                except:
                    continue
            if link: break
            time.sleep(1)
        driver.quit()
    except Exception as e:
        print(f"Lỗi: {e}")

    # Dự phòng bằng yt-dlp nếu soi mạng không ra
    if not link:
        cmd = ['yt-dlp', '-g', '--referer', target_url, target_url]
        res = subprocess.run(cmd, capture_output=True, text=True)
        link = res.stdout.strip()

    if link and "http" in link:
        update_gist(link, match_name)
    else:
        send_telegram(f"❌ Bế tắc với {match_name}. Không tìm thấy luồng live hợp lệ.")

if __name__ == "__main__":
    get_link()
