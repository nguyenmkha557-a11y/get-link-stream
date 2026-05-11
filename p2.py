import os
import subprocess
import requests
import json
import time
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
    # Thử lấy dữ liệu từ link worker
    url = f"https://{cf_worker_name}.nguyenmanhcuong83ro.workers.dev/"
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
    json_string = json.dumps(current_data, ensure_ascii=False)
    
    # FIX: Để export default sát lề trái, không dùng thụt lề thụ động của Python
    worker_script = f'export default {{ async fetch(request, env) {{ const data = {json_string}; return new Response(JSON.stringify(data), {{ headers: {{ "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store, no-cache, must-revalidate", "Access-Control-Allow-Origin": "*" }} }}); }} }};'

    url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/workers/scripts/{cf_worker_name}"
    
    headers = {
        "Authorization": f"Bearer {cf_api_token}",
        "Content-Type": "application/javascript"
    }

    # Gửi PUT request
    res = requests.put(url, headers=headers, data=worker_script.encode('utf-8'))
    
    if res.status_code == 200:
        print("✅ Thành công!")
        send_telegram(f"✅ Cloudflare Updated!\n⚽ {match_name}")
    else:
        # In ra nội dung lỗi cụ thể để biết Cloudflare chê chỗ nào
        error_detail = res.text
        print(f"❌ Lỗi Cloudflare {res.status_code}: {error_detail}")
        send_telegram(f"❌ Lỗi Cloudflare {res.status_code}: {error_detail[:100]}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    if not target_url: return

    if ".m3u8" in target_url.lower():
        update_cloudflare_worker_json(target_url, match_name)
        return


    link = None


    if link:
        update_cloudflare_worker_json(link, match_name)
    else:
        print("Không tìm thấy link")

if __name__ == "__main__":
    get_link()
