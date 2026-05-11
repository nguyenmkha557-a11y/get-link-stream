import os
import requests
import json

def get_current_worker_m3u():
    cf_worker_name = os.getenv('CF_WORKER_NAME')
    # Link truy cập worker của bạn
    url = f"https://{cf_worker_name}.nguyenmanhcuong83ro.workers.dev/"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and "#EXTM3U" in res.text:
            return res.text.strip()
    except:
        pass
    # Nếu chưa có nội dung, trả về dòng đầu tiên mặc định
    return '#EXTM3U url-tvg="https://vnepg.site/epg.xml"'

def update_cloudflare_worker_m3u(new_link, match_name):
    cf_account_id = os.getenv('CF_ACCOUNT_ID', '').strip()
    cf_worker_name = os.getenv('CF_WORKER_NAME', '').strip()
    cf_api_token = os.getenv('CF_API_TOKEN', '').strip()
    
    # 1. Lấy nội dung M3U hiện tại
    current_m3u = get_current_worker_m3u()
    
    # 2. Tạo đoạn nội dung mới cho trận đấu này
    # Bạn có thể thay đổi logo mặc định ở đây
    logo = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B_Sport_2015.png"
    new_entry = f'\n#EXTINF:-1 group-title="THỂ THAO" tvg-logo="{logo}", {match_name}\n{new_link.strip()}'
    
    # 3. Nối nội dung mới vào nội dung cũ
    updated_content = current_m3u + new_entry
    
    # 4. Tạo mã Script cho Cloudflare (Dùng định dạng Service Worker để tránh lỗi 'export')
    # Lưu ý: Content-Type đổi thành application/x-mpegurl
    worker_script = f'''
addEventListener("fetch", event => {{
  event.respondWith(handleRequest(event.request))
}});

async function handleRequest(request) {{
  const m3uContent = `{updated_content}`;
  return new Response(m3uContent, {{
    headers: {{
      "Content-Type": "application/x-mpegurl; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "no-store, no-cache, must-revalidate"
    }}
  }});
}}
'''

    url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/workers/scripts/{cf_worker_name}"
    headers = {
        "Authorization": f"Bearer {cf_api_token}",
        "Content-Type": "application/javascript"
    }

    res = requests.put(url, headers=headers, data=worker_script.encode('utf-8'))
    
    if res.status_code == 200:
        print(f"✅ Đã thêm trận đấu: {match_name}")
    else:
        print(f"❌ Lỗi {res.status_code}: {res.text}")

if __name__ == "__main__":
    m_url = os.getenv('MATCH_URL')
    m_name = os.getenv('MATCH_NAME', 'Kênh mới')
    
    if m_url:
        update_cloudflare_worker_m3u(m_url, m_name)
    else:
        print("❌ Không có link để update.")
