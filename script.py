import os
import subprocess
import requests

def update_gist(new_link):
    gist_id = os.getenv('GIST_ID')
    gist_token = os.getenv('GIST_TOKEN')
    
    if not gist_id or not gist_token:
        print("Thiếu GIST_ID hoặc GIST_TOKEN!")
        return

    # Cấu trúc nội dung file M3U của bạn
    # Mình dùng f-string để chèn link mới vào dòng cuối cùng
    m3u_content = f"""#EXTM3U url-tvg="https://vnepg.site/epg.xml"
#EXTINF:-1 group-title="THỂ THAO QUỐC TẾ" tvg-id="skyf1" tvg-logo="https://r2.thesportsdb.com/images/media/channel/logo/p5csyn1620551587.png",Sky Sport F1
http://line.watchtivo-8k.com:80/play/live.php?mac=00:1A:79:3F:0C:96&stream=1149423&extension=ts&play_token=1jkVQWGCqc
#EXTINF:-1 group-title="THỂ THAO QUỐC TẾ" tvg-id="skytennis" tvg-logo="https://e0.365dm.com/24/01/2048x1152/skysports-sky-sports-tennis_6437040.jpg",Sky Sport Tennis
http://line.watchtivo-8k.com:80/play/live.php?mac=00:1A:79:3F:0C:96&stream=1149433&extension=ts&play_token=Y1kv3yxPS8
#EXTINF:-1 group-title="THỂ THAO QUỐC TẾ" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B_Sport_2015.png",Canal+ Sport
{new_link}"""

    url = f"https://api.github.com/gists/{gist_id}"
    headers = {
        "Authorization": f"token {gist_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # "link_stream.txt" là tên file bên trong Gist của bạn, bạn có thể đổi thành "list.m3u"
    data = {
        "files": {
            "playlist.json": {
                "content": m3u_content
            }
        }
    }
    
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        print("✅ Đã cập nhật danh sách M3U vào Gist thành công!")
    else:
        print(f"❌ Lỗi: {response.status_code} - {response.text}")

def get_link():
    # Bạn nhớ thay link trận đấu đang diễn ra vào đây để test nhé
    target_url = "https://bunchatv4.net/truc-tiep/manchester-city-vs-brentford-2330-09-05-2026/601447441"
    
    cmd = [
        'yt-dlp', '-g', 
        '--referer', 'https://bunchatv4.net/', 
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        target_url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    link = result.stdout.strip()
    
    if link and "http" in link:
        print(f"Tìm thấy link mới: {link}")
        update_gist(link)
    else:
        print("Không lấy được link stream.")

if __name__ == "__main__":
    get_link()
