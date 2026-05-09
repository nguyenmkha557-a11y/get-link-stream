import os
import subprocess
import requests

def get_current_gist_content(gist_id, gist_token):
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = response.json().get('files', {})
        # Thay 'link_stream.txt' bằng tên file chính xác trong Gist của bạn
        file_data = files.get('playlist.m3u', {})
        return file_data.get('content', '')
    return ""

def update_gist(new_link, match_name):
    gist_id = os.getenv('GIST_ID')
    gist_token = os.getenv('GIST_TOKEN')
    
    # 1. Lấy nội dung cũ đang có trên Gist
    current_content = get_current_gist_content(gist_id, gist_token)
    
    # Nếu Gist trống, khởi tạo header M3U
    if not current_content.strip():
        current_content = '#EXTM3U url-tvg="https://vnepg.site/epg.xml"'

    # 2. Tạo 2 dòng mới cho trận đấu
    new_entry = f'\n#EXTINF:-1 group-title="THỂ THAO QUỐC TẾ" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B_Sport_2015.png",{match_name}\n{new_link}'
    
    # 3. Cộng dồn nội dung
    updated_content = current_content.strip() + new_entry

    # 4. Gửi nội dung đã được nối dài lên lại Gist
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {gist_token}"}
    data = {"files": {"playlist.json": {"content": updated_content}}}
    
    res = requests.patch(url, headers=headers, json=data)
    if res.status_code == 200:
        print(f"✅ Đã thêm trận {match_name} vào danh sách!")
    else:
        print(f"❌ Lỗi cập nhật: {res.status_code}")

def get_link():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')
    
    cmd = ['yt-dlp', '-g', '--referer', 'https://bunchatv4.net/', target_url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    link = result.stdout.strip()
    
    if link and "http" in link:
        update_gist(link, match_name)
    else:
        print("Không lấy được link.")

if __name__ == "__main__":
    get_link()
