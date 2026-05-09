import subprocess

def test_get_link():
    # Link trận đấu để test
    target_url = "https://bunchatv4.net/truc-tiep/sydney-fc-vs-newcastle-jets-1640-09-05-2026/601445242"
    
    print(f"--- ĐANG TEST LẤY LINK TỪ: {target_url} ---")
    
    try:
        # Chạy yt-dlp để lấy link
        # Thêm --referer để giả lập truy cập từ web gốc
        cmd = ['yt-dlp', '-g', '--referer', 'https://bunchatv4.net/', target_url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        link = result.stdout.strip()
        
        if link and "http" in link:
            print("\n✅ THÀNH CÔNG! ĐÃ TÌM THẤY LINK STREAM:")
            print(link)
            print("\n--------------------------------------")
        else:
            print("\n❌ THẤT BẠI: Không lấy được link.")
            print(f"Lỗi chi tiết từ hệ thống: {result.stderr}")
            
    except Exception as e:
        print(f"⚠️ Lỗi code: {str(e)}")

if __name__ == "__main__":
    test_get_link()
