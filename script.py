import os
import subprocess
import requests

def send_telegram(message):
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    if not token or not chat_id:
        print("Thiếu Token hoặc Chat ID trong Secrets!")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def get_link():
    # Link trận đấu cụ thể (Bạn có thể thay đổi link này)
    target_url = "https://bunchatv4.net/truc-tiep/sydney-fc-vs-newcastle-jets-1640-09-05-2026/601445242"
    
    try:
        # Chạy yt-dlp để lấy link stream trực tiếp
        # Thêm --referer để tránh bị chặn
        cmd = ['yt-dlp', '-g', '--referer', 'https://bunchatv4.net/', target_url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        link = result.stdout.strip()
        
        if link and "http" in link:
            send_telegram(f"✅ Đã lấy được link stream:\n\n{link}")
        else:
            send_telegram("❌ Không tìm thấy link stream. Có thể trận đấu chưa bắt đầu hoặc web đã đổi cấu trúc.")
            print(f"Lỗi log: {result.stderr}")
            
    except Exception as e:
        send_telegram(f"⚠️ Lỗi hệ thống: {str(e)}")

if __name__ == "__main__":
    get_link()
