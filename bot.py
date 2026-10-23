import time
import requests
import threading
from flask import Flask

# --- MİNİ WEB SUNUCUSU ---
app = Flask(__name__)

@app.route('/')
def home():
    return "IG Status Monitor Bot is Running!"

def run_web():
    app.run(host="0.0.0.0", port=10000)
# -------------------------

TELEGRAM_TOKEN = "8615223587:AAF3-6mxihxBwZZ_cUU8BRwdt5dBOfB-E3M"
CHAT_ID = "1982331582"

unban_list = set()
ban_list = set()

last_update_id = 0

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Telegram error: {e}")

def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=3)
        return response.status_code == 200
    except Exception as e:
        print(f"Instagram check error (@{username}): {e}")
        return False

def process_telegram_commands():
    global last_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 1}
    try:
        res = requests.get(url, params=params, timeout=3)
        data = res.json()
        if data.get("ok"):
            for update in data.get("result", []):
                last_update_id = update["update_id"]
                msg = update.get("message", {})
                text = msg.get("text", "").strip()
                chat_id = str(msg.get("chat", {}).get("id", ""))
                
                if chat_id != CHAT_ID:
                    continue
                    
                # /unban
                if text.startswith("/unban"):
                    parts = text.split()
                    if len(parts) > 1:
                        username = parts[1].replace("@", "").strip()
                        unban_list.add(username)
                        if username in ban_list:
                            ban_list.remove(username)
                        send_telegram(f"👀 <b>Unban Takibine Eklendi:</b> @{username}\n(Açılması bekleniyor)")
                    else:
                        send_telegram("⚠️ Kullanıcı adı girin. Örnek: /unban @kullaniciadi")
                        
                # /ban
                elif text.startswith("/ban"):
                    parts = text.split()
                    if len(parts) > 1:
                        username = parts[1].replace("@", "").strip()
                        ban_list.add(username)
                        if username in unban_list:
                            unban_list.remove(username)
                        send_telegram(f"👀 <b>Ban Takibine Eklendi:</b> @{username}\n(Kapanması bekleniyor)")
                    else:
                        send_telegram("⚠️ Kullanıcı adı girin. Örnek: /ban @kullaniciadi")
                        
                # /remove
                elif text.startswith("/remove"):
                    parts = text.split()
                    if len(parts) > 1:
                        username = parts[1].replace("@", "").strip()
                        removed = False
                        if username in unban_list:
                            unban_list.remove(username)
                            removed = True
                        if username in ban_list:
                            ban_list.remove(username)
                            removed = True
                            
                        if removed:
                            send_telegram(f"🗑️ <b>Takip Listesinden Silindi:</b> @{username}")
                        else:
                            send_telegram(f"⚠️ @{username} zaten takip listesinde yoktu.")
                    else:
                        send_telegram("⚠️ Kullanıcı adı girin. Örnek: /remove @kullaniciadi")

                # /list
                elif text.startswith("/list"):
                    msg_text = "📋 <b>Takip Edilen Hesaplar:</b>\n\n"
                    msg_text += f"🟢 <b>Unban Bekleyenler:</b> {list(unban_list) if unban_list else 'Boş'}\n"
                    msg_text += f"🔴 <b>Ban Bekleyenler:</b> {list(ban_list) if ban_list else 'Boş'}"
                    send_telegram(msg_text)
    except Exception as e:
        print(f"Command processing error: {e}")

def main():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
    send_telegram("🚀 <b>Bot Hazır! Komutlar güncellendi.</b>")
    
    while True:
        try:
            process_telegram_commands()
            
            for username in list(unban_list):
                process_telegram_commands()
                is_active = check_instagram(username)
                if is_active:
                    send_telegram(f"✅ <b>Hesap Açıldı!</b> @{username}\nhttps://www.instagram.com/{username}")
                    unban_list.remove(username)
                    
            for username in list(ban_list):
                process_telegram_commands()
                is_active = check_instagram(username)
                if not is_active:
                    send_telegram(f"❌ <b>Hesap Kapandı/Banned!</b> @{username}\nhttps://www.instagram.com/{username}")
                    ban_list.remove(username)
                    
            time.sleep(10)
            
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
