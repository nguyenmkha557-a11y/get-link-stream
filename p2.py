import os
import requests
import json

def send_telegram(message):
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, data={"chat_id": chat_id, "text": message})
        except: pass

def get_current_worker_json():
    cf_worker_name = os.getenv('CF_WORKER_NAME')
    # Thử lấy link trực tiếp. Nếu lỗi 404 thì trả về playlist rỗng
    url = f"https://{cf_worker_name}.nguyenmanhcuong83ro.workers.dev/"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return {"name": "Playlist Live", "items": []}

def update_cloudflare_worker_json(new_link, match_name):
    # Lấy biến môi trường từ GitHub Actions
    cf_account_id = os.getenv('CF_ACCOUNT_ID', '').strip()
    cf_worker_name = os.getenv('CF_WORKER_NAME', '').strip()
    cf_api_token = os.getenv('CF_API_TOKEN', '').strip()
    
    # Kiểm tra xem có lấy được biến không để tránh link bị trống gây 404
    if not cf_account_id or not cf_worker_name:
        print("❌ Lỗi: Thiếu CF_ACCOUNT_ID hoặc CF_WORKER_NAME trong Secrets!")
        return

    current_data = get_current_worker_json()
    new_item = {
        "title": match_name,
        "group": "LIVE",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B_Sport_2015.png",
        "url": new_link.strip()
    }
    current_data["items"].append(new_item)
    
    json_string = json.dumps(current_data, ensure_ascii=False)
    worker_script = f'export default {{ async fetch(request, env) {{ const data = {json_string}; return new Response(JSON.stringify(data), {{ headers: {{ "Content-Type": "application/json; charset=utf-8", "Access-Control-Allow-Origin": "*" }} }}); }} }};'

    # URL API chuẩn của Cloudflare
    url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/workers/scripts/{cf_worker_name}"
    
    headers = {
        "Authorization": f"Bearer {cf_api_token}",
        "Content-Type": "application/javascript"
    }

    res = requests.put(url, headers=headers, data=worker_script.encode('utf-8'))
    
    if res.status_code == 200:
        print("✅ Thành công!")
        send_telegram(f"✅ Cloudflare Updated!\n⚽ {match_name}")
    else:
        print(f"❌ Lỗi {res.status_code}: {res.text}")
        send_telegram(f"❌ Lỗi Cloudflare {res.status_code}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    
    # Giả lập link để test ghi Cloud
    link = "https://link-test-m3u8.com/live.m3u8"
    
    if target_url and ".m3u8" in target_url.lower():
        link = target_url

    update_cloudflare_worker_json(link, match_name)

if __name__ == "__main__":
    get_link()
