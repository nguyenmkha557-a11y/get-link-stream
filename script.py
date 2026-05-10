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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": target_url
    }

    print(f"🔍 Đang quét sâu: {match_name}")
    
    try:
        # Bước 1: Tải mã nguồn trang chính
        response = requests.get(target_url, headers=headers, timeout=15)
        html = response.text

        # Bước 2: Tìm link .m3u8 trực tiếp (nếu có)
        found_links = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', html)
        
        # Bước 3: Nếu không có m3u8, tìm các link Iframe (thường là các link stream ẩn)
        if not found_links:
            print("Không thấy m3u8, đang tìm Iframe ẩn...")
            # Tìm các link trong thẻ src của iframe hoặc các link chứa chữ 'embed', 'player', 'live'
            iframes = re.findall(r'src=["\'](https?://[^"\']+)["\']', html)
            for frame_url in iframes:
                if "facebook" in frame_url or "google" in frame_url: continue
                try:
                    print(f"Đang chui vào iframe: {frame_url}")
                    f_res = requests.get(frame_url, headers={"User-Agent": headers["User-Agent"], "Referer": target_url}, timeout=10)
                    found_links += re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', f_res.text)
                except:
                    continue

        # Bước 4: Xử lý kết quả
        if found_links:
            # Lấy link đầu tiên không phải link rác
            final_link = None
            for l in found_links:
                clean_link = l.replace('\\/', '/')
                if "m3u8" in clean_link and "http" in clean_link:
                    final_link = clean_link
                    break
            
            if final_link:
                update_gist(final_link, match_name)
                return

        # Bước 5: Nếu tất cả thất bại, dùng yt-dlp làm phương án cuối
        cmd = ['yt-dlp', '-g', '--referer', target_url, target_url]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if "http" in res.stdout:
            update_gist(res.stdout.strip(), match_name)
            return

    except Exception as e:
        print(f"Lỗi: {e}")

    send_telegram(f"❌ Vẫn không lấy được link cho: {match_name}\nĐại ca thử lấy link Server khác trên web rồi gửi lại xem sao.")

if __name__ == "__main__":
    get_link()
