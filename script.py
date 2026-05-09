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
            print("✅ Đã nhắn link vào Telegram!")
        except Exception as e:
            print(f"❌ Lỗi Telegram: {e}")

def update_gist(new_link):
    gist_id = os.getenv('GIST_ID')
    gist_token = os.getenv('GIST_TOKEN')
    if not gist_id or not gist_token:
        return

    m3u_content = f"""#EXTM3U url-tvg="https://vnepg.site/epg.xml"
#EXTINF:-1 group-title="THỂ THAO QUỐC TẾ" tvg-id="skyf1" tvg-logo="https://r2.thesportsdb.com/images/media/channel/logo/p5csyn1620551587.png",Sky Sport F1
http://line.watchtivo-8k.com:80/play/live.php?mac=00:1A:79:3F:0C:96&stream=1149423&extension=ts&play_token=1jkVQWGCqc
#EXTINF:-1 group-title="THỂ THAO QUỐC TẾ" tvg-id="skytennis" tvg-logo="https://e0.365dm.com/24/01/2048x1152/skysports-sky-sports-tennis_6437040.jpg",Sky Sport Tennis
http://line.watchtivo-8k.com:80/play/live.php?mac=00:1A:79:3F:0C:96&stream=1149433&extension=ts&play_token=Y1kv3yxPS8
#EXTINF:-1 group-title="THỂ THAO QUỐC TẾ" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B_Sport_2015.png",Canal+ Sport
{new_link}"""

    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    data = {"files": {"link_stream.txt": {"content": m3u_content}}}
    
    requests.patch(url, headers=headers, json=data)
    print("✅ Đã cập nhật Gist!")

def get_link():
    # Thay vì viết cứng link, ta lấy từ ENV mà GitHub truyền vào
    target_url = os.getenv('MATCH_URL')
    
    if not target_url:
        print("Không có link trận đấu để chạy!")
        return
    
    print(f"Đang xử lý trận: {target_url}")
    
    cmd = [
        'yt-dlp', '-g', 
        '--referer', 'https://bunchatv4.net/', 
        target_url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    link = result.stdout.strip()
    
    if link and "http" in link:
        update_gist(link)
        send_telegram(f"⚽ Cập nhật thành công!\nLink mới: {link}")
    else:
        send_telegram("❌ Lỗi: Không tìm thấy stream cho link bạn gửi.")

if __name__ == "__main__":
    get_link()
