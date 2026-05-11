import os
import requests
import json

def update_cloudflare_worker_json(new_link, match_name):
    cf_account_id = os.getenv('CF_ACCOUNT_ID', '').strip()
    cf_worker_name = os.getenv('CF_WORKER_NAME', '').strip()
    cf_api_token = os.getenv('CF_API_TOKEN', '').strip()
    
    # Giả định lấy dữ liệu cũ hoặc tạo mới
    # Để test nhanh, mình tạo playlist mới luôn, bạn có thể tích hợp hàm get_current_worker_json sau
    current_data = {"name": "Playlist Live", "items": []}
    new_item = {
        "title": match_name,
        "group": "LIVE",
        "url": new_link.strip()
    }
    current_data["items"].append(new_item)
    
    json_string = json.dumps(current_data, ensure_ascii=False)
    
    # FILE SỬA TẠI ĐÂY: Dùng định dạng cũ để tránh lỗi "Unexpected token export"
    worker_script = f'addEventListener("fetch", event => {{ event.respondWith(handleRequest(event.request)) }}); async function handleRequest(request) {{ const data = {json_string}; return new Response(JSON.stringify(data), {{ headers: {{ "Content-Type": "application/json; charset=utf-8", "Access-Control-Allow-Origin": "*" }} }}); }}'

    url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/workers/scripts/{cf_worker_name}"
    headers = {
        "Authorization": f"Bearer {cf_api_token}",
        "Content-Type": "application/javascript"
    }

    res = requests.put(url, headers=headers, data=worker_script.encode('utf-8'))
    
    if res.status_code == 200:
        print("✅ Đã cập nhật Cloudflare thành công!")
    else:
        print(f"❌ Lỗi {res.status_code}: {res.text}")

if __name__ == "__main__":
    m_url = os.getenv('MATCH_URL', 'https://test.m3u8')
    m_name = os.getenv('MATCH_NAME', 'Test Match')
    update_cloudflare_worker_json(m_url, m_name)
