import os
import subprocess
import requests

def update_gist(content):
    gist_id = os.getenv('GIST_ID')
    gist_token = os.getenv('GIST_TOKEN')
    
    if not gist_id or not gist_token:
        print("Thiếu GIST_ID hoặc GIST_TOKEN!")
        return

    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    
    # Chuẩn bị nội dung file trong Gist (giữ tên file gốc của bạn)
    data = {
        "files": {
            "link_stream.txt": {  # Bạn có thể đổi tên file hiển thị trong Gist
                "content": content
            }
        }
    }
    
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        print("✅ Đã cập nhật link vào Gist thành công!")
    else:
        print(f"❌ Lỗi cập nhật Gist: {response.status_code}")

def get_link():
    target_url = "https://bunchatv4.net/truc-tiep/manchester-city-vs-brentford-2330-09-05-2026/601447441"
    
    cmd = [
        'yt-dlp', '-g', 
        '--referer', 'https://bunchatv4.net/', 
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        target_url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    link = result.stdout.strip()
    
    if link and "http" in link:
        print(f"Tìm thấy link: {link}")
        update_gist(link) # Gọi hàm cập nhật Gist
    else:
        print("Không tìm thấy link.")

if __name__ == "__main__":
    get_link()
