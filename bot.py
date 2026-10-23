import time
import requests
import threading
from flask import Flask

# --- MINI WEB SERVER (Render Port Requirement) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "IG Status Monitor Bot is Running!"

def run_web():
    app.run(host="0.0.0.0", port=10000)
# --------------------------------------------------

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
    # Professional API check to completely eliminate false "closed" alarms on active accounts
    api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "X-IG-App-ID": "936619743392459",
        "Accept": "application/json",
        "Referer": f"https://www.instagram.com/{username}/"
    }
    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            user_data = data.get("data", {}).get("user")
            if user_data is not None:
                return "ACTIVE"
            else:
                return "CLOSED"
        elif response.status_code == 404:
            return "CLOSED"
        else:
            # Fallback check to prevent false alarms during temporary rate limits
            fallback_url = f"https://www.instagram.com/{username}/"
            fb_res = requests.get(fallback_url, headers={"User-Agent": headers["User-Agent"]}, timeout=5)
            if fb_res.status_code == 200:
                return "ACTIVE"
            elif fb_res.status_code == 404:
                return "CLOSED"
            else:
                return "ACTIVE"
    except Exception as e:
        print(f"Instagram check error (@{username}): {e}")
        return "ERROR"

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
                    
                # /unban command
                if text.startswith("/unban"):
                    parts = text.split()
                    if len(parts) > 1:
                        username = parts[1].replace("@", "").strip()
                        unban_list.add(username)
                        if username in ban_list:
                            ban_list.remove(username)
                        send_telegram(f"👀 <b>Added to Unban Tracking:</b> @{username}\n(Waiting for account to open)")
                    else:
                        send_telegram("⚠️ Please specify a username. Example: /unban @username")
                        
                # /ban command
                elif text.startswith("/ban"):
                    parts = text.split()
                    if len(parts) > 1:
                        username = parts[1].replace("@", "").strip()
                        ban_list.add(username)
                        if username in unban_list:
                            unban_list.remove(username)
                        send_telegram(f"👀 <b>Added to Ban Tracking:</b> @{username}\n(Waiting for account to close)")
                    else:
                        send_telegram("⚠️ Please specify a username. Example: /ban @username")
                        
                # /remove command
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

                # /list command
                elif text.startswith("/list"):
                    msg_text = "📋 <b>Tracked Accounts:</b>\n\n"
                    msg_text += f"🟢 <b>Waiting for Unban:</b> {list(unban_list) if unban_list else 'Empty'}\n"
                    msg_text += f"🔴 <b>Waiting for Ban:</b> {list(ban_list) if ban_list else 'Empty'}"
                    send_telegram(msg_text)
    except Exception as e:
        print(f"Command processing error: {e}")

def main():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
    send_telegram("🚀 <b>Bot Updated & Fully Operational!</b>")
    
    while True:
        try:
            process_telegram_commands()
            
            current_unban = list(unban_list)
            for username in current_unban:
                if username not in unban_list:
                    continue
                process_telegram_commands()
                status = check_instagram(username)
                if status == "ACTIVE":
                    send_telegram(f"✅ <b>Account Activated!</b> @{username}\nhttps://www.instagram.com/{username}")
                    unban_list.discard(username)
                    
            current_ban = list(ban_list)
            for username in current_ban:
                if username not in ban_list:
                    continue
                process_telegram_commands()
                status = check_instagram(username)
                if status == "CLOSED":
                    send_telegram(f"❌ <b>Account Banned/Closed!</b> @{username}\nhttps://www.instagram.com/{username}")
                    ban_list.discard(username)
                    
            time.sleep(15)
            
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
