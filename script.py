import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import re
import time

def get_link_selenium():
    target_url = os.getenv('MATCH_URL')
    match_name = os.getenv('MATCH_NAME', 'Trận đấu mới')

    # Cấu hình Chrome chạy ngầm (không màn hình)
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    link = None
    try:
        print(f"📡 Đang dùng Chrome ảo truy cập: {target_url}")
        driver.get(target_url)
        
        # Đợi 10 giây cho trang web tải xong và chạy script ngầm
        time.sleep(10) 
        
        # Lấy toàn bộ log mạng hoặc mã nguồn sau khi render
        html_source = driver.page_source
        
        # Quét link m3u8
        found = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', html_source)
        if found:
            for l in found:
                l = l.replace('\\/', '/')
                if "m3u8" in l and "apple" not in l:
                    link = l
                    break
    finally:
        driver.quit()

    if link:
        update_gist(link, match_name)
    else:
        # Nếu Selenium vẫn không thấy, quay lại dùng yt-dlp làm dự phòng
        # (Giữ lại hàm cũ ở đây...)
