import os
import subprocess
import requests

def send_telegram(message):
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
            print("✅ Đã gửi thông báo Telegram")
        except:
            print("❌ Lỗi gửi Telegram")

def get_current_gist_content(gist_id, gist_token):
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            files = response.json().get('files', {})
            # Chú ý: Tên file 'link_stream.txt' phải khớp với tên trên Gist của bạn
            for file_name in files:
                return files[file_name].get('content', '')
    except:
        pass
    return ""

def update_gist(new_link, match_name):
    gist_id = os.getenv('GIST_ID')
    gist_token = os.getenv('GIST_TOKEN')
    
    # 1. Lấy nội dung cũ
    current_content = get_current_gist_content(gist_id, gist_token)
    
    if not current_content.strip():
        current_content = '#EXTM3U url-tvg="https://vnepg.site/epg.xml"'

    # 2. Tạo nội dung mới (Nối thêm vào cuối)
    new_entry = f'\n#EXTINF:-1 group-title="THỂ THAO QUỐC TẾ" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B_Sport_2015.png",{match_name}\n{new_link}'
    updated_content = current_content.strip() + new_entry

    # 3. Ghi đè nội dung ĐÃ NỐI DÀI lên Gist
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    
    # Lấy tên file đầu tiên trong Gist để ghi đè chính xác
    res_get = requests.get(url, headers=headers).json()
    first_file_name = list(res_get['files'].keys())[0]
    
    data = {"files": {first_file_name: {"content": updated_content}}}
    
    res = requests.patch(url, headers=headers, json=data)
    if res.status_code == 200:
        send_telegram(f"✅ Đã thêm trận đấu thành công!\n⚽ Trận: {match_name}\n🔗 Link: {new_link}")
    else:
        send_telegram(f"❌ Lỗi cập nhật Gist: {res.status_code}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    
    if not target_url: return

    # Cấu hình "vượt rào"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Xác định Referer linh hoạt
    referer = "https://bunchatv4.net/"
    if "quechoa" in target_url:
        # Lấy domain chính của quechoa (ví dụ quechoa10.live)
        from urllib.parse import urlparse
        domain = urlparse(target_url).netloc
        referer = f"https://{domain}/"

    # Lệnh yt-dlp nâng cao
    cmd = [
        'yt-dlp', 
        '-g', 
        '--referer', referer,
        '--user-agent', headers["User-Agent"],
        '--no-check-certificates',
        '--quiet',
        target_url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    link = result.stdout.strip()
    
    # Nếu yt-dlp thất bại, thử tìm link .m3u8 thủ công bằng regex (dự phòng)
    if not link or "http" not in link:
        print("Thử phương pháp dự phòng...")
        # (Phần này có thể thêm sau nếu trang web quá khó)
    
    if link and "http" in link:
        update_gist(link, match_name)
    else:
        send_telegram(f"❌ Không tìm thấy link cho: {match_name}\nTrang này bảo mật cao hơn dự kiến.")

if __name__ == "__main__":
    get_link()
