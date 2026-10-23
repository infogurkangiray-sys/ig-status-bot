import time
import requests

# Telegram Bilgilerin
TELEGRAM_TOKEN = "8615223587:AAF3-6mxihxBwZZ_cUU8BRwdt5dBOfB-E3M"
CHAT_ID = "1982331582"

# Dinamik Takip Listeleri
unban_list = set() # Açılması beklenenler (Kapalı hesaplar)
ban_list = set()   # Kapanması beklenenler (Açık hesaplar)

last_update_id = 0

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False

def process_telegram_commands():
    global last_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 2}
    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
        if data.get("ok"):
            for update in data.get("result", []):
                last_update_id = update["update_id"]
                msg = update.get("message", {})
                text = msg.get("text", "").strip()
                chat_id = str(msg.get("chat", {}).get("id", ""))
                
                # Sadece senin sohbetinden gelen komutları dinle
                if chat_id != CHAT_ID:
                    continue
                    
                # 1. UNBAN KOMUTU (Kapalı hesabı izle)
                if text.startswith("/unban"):
                    parts = text.split()
                    if len(parts) > 1:
                        username = parts[1].replace("@", "").strip()
                        unban_list.add(username)
                        if username in ban_list:
                            ban_list.remove(username)
                        send_telegram(f"👀 <b>Tracking for Unban (Waiting to Open):</b> @{username}")
                    else:
                        send_telegram("⚠️ Please specify a username. Example: /unban @username")
                        
                # 2. BAN KOMUTU (Açık hesabı izle)
                elif text.startswith("/ban"):
                    parts = text.split()
                    if len(parts) > 1:
                        username = parts[1].replace("@", "").strip()
                        ban_list.add(username)
                        if username in unban_list:
                            unban_list.remove(username)
                        send_telegram(f"👀 <b>Tracking for Ban (Waiting to Close):</b> @{username}")
                    else:
                        send_telegram("⚠️ Please specify a username. Example: /ban @username")
                        
                # 3. LİSTEDEN SİLME KOMUTU
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
                            send_telegram(f"🗑️ <b>Removed from tracking:</b> @{username}")
                        else:
                            send_telegram(f"⚠️ @{username} was not found in any tracking list.")
                    else:
                        send_telegram("⚠️ Please specify a username. Example: /remove @username")

                # 4. LİSTeleme KOMUTU
                elif text.startswith("/list"):
                    msg_text = "📋 <b>Tracked Accounts:</b>\n\n"
                    msg_text += f"🟢 <b>Waiting for Unban:</b> {list(unban_list)}\n"
                    msg_text += f"🔴 <b>Waiting for Ban:</b> {list(ban_list)}"
                    send_telegram(msg_text)
    except Exception as e:
        print(f"Command error: {e}")

def main():
    send_telegram("🚀 <b>IG Status Monitor Bot is Active & Interactive!</b>\n\nCommands:\n/unban @username\n/ban @username\n/remove @username\n/list")
    
    while True:
        try:
            # 1. Telegram'dan gelen komutları kontrol et
            process_telegram_commands()
            
            # 2. Kapalı hesaplar açıldı mı kontrol et (Unban listesi)
            for username in list(unban_list):
                is_active = check_instagram(username)
                if is_active:
                    msg = (
                        f"✅ <b>Account Activated</b> 👤 <b>Username:</b> @{username}\n"
                        f"🔗 <b>Link:</b> https://www.instagram.com/{username}"
                    )
                    send_telegram(msg)
                    unban_list.remove(username)
                    
            # 3. Açık hesaplar kapandı mı kontrol et (Ban listesi)
            for username in list(ban_list):
                is_active = check_instagram(username)
                if not is_active:
                    msg = (
                        f"❌ <b>Account Banned</b> 👤 <b>Username:</b> @{username}\n"
                        f"🔗 <b>Link:</b> https://www.instagram.com/{username}"
                    )
                    send_telegram(msg)
                    ban_list.remove(username)
                    
            time.sleep(30)
            
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
