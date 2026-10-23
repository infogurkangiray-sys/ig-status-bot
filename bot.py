import time
import requests

# Telegram Bilgilerin
TELEGRAM_TOKEN = "8615223587:AAF3-6mxihxBwZZ_cUU8BRwdt5dBOfB-E3M"
CHAT_ID = "1982331582"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram gönderme hatası: {e}")

def check_instagram():
    print("Hesap durumu kontrol ediliyor...")
    # Buraya Instagram kontrol kodların gelecek

def main():
    send_telegram("🚀 IG Status Monitor Botu Aktif ve 7/24 Çalışıyor!")
    while True:
        try:
            check_instagram()
            time.sleep(60) # 60 saniyede bir kontrol eder
        except Exception as e:
            print(f"Sistem hatası: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
