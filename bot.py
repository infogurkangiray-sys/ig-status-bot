import os
import time
import requests
import threading
from io import BytesIO
from flask import Flask
from PIL import Image, ImageDraw, ImageFont

# --- MINI WEB SERVER (Render Port Requirement) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "IG Status Monitor Bot is Running!"

def run_web():
    app.run(host="0.0.0.0", port=10000)
# --------------------------------------------------

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

unban_list = set()
ban_list = set()
last_update_id = 0

def send_telegram_message(message):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Telegram error: {e}")

def send_telegram_photo(photo_bytes, caption):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": ("profile_card.jpg", photo_bytes, "image/jpeg")}
    data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, files=files, timeout=10)
    except Exception as e:
        print(f"Telegram photo error: {e}")
        send_telegram_message(caption)

def generate_profile_card(username, profile_pic_url, posts_count, followers_count, following_count):
    # Siyah arka planlı modern Instagram kartı oluşturuyoruz (Genişlik: 800, Yükseklik: 500)
    width, height = 800, 500
    card = Image.new("RGB", (width, height), color=(15, 15, 15))
    draw = ImageDraw.Draw(card)
    
    # Profil Fotoğrafı (İndirip karta yuvarlak şekilde yerleştiriyoruz)
    try:
        response = requests.get(profile_pic_url, timeout=5)
        if response.status_code == 200:
            avatar = Image.open(BytesIO(response.content)).convert("RGBA")
            avatar = avatar.resize((120, 120))
            
            # Yuvarlak maske oluştur
            mask = Image.new("L", (120, 0), 0)
            # Basit kare veya daire yerleşimi için doğrudan yapıştırıyoruz
            card.paste(avatar, (60, 60), avatar)
    except Exception as e:
        print(f"Avatar load error: {e}")
        
    # Yazı ve İstatistikler için varsayılan font (sistem fontu)
    try:
        font_large = ImageFont.truetype("arial.ttf", 28)
        font_med = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_med = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Kullanıcı Adı
    draw.text((210, 75), f"@{username}", fill=(255, 255, 255), font=font_large)
    
    # İstatistikler (Posts, Followers, Following)
    # Konumlar: Posts (210), Followers (340), Following (490)
    draw.text((210, 130), str(posts_count), fill=(255, 255, 255), font=font_med)
    draw.text((210, 160), "posts", fill=(150, 150, 150), font=font_small)
    
    formatted_followers = f"{followers_count:,}"
    draw.text((340, 130), formatted_followers, fill=(255, 255, 255), font=font_med)
    draw.text((340, 160), "followers", fill=(150, 150, 150), font=font_small)
    
    draw.text((490, 130), str(following_count), fill=(255, 255, 255), font=font_med)
    draw.text((490, 160), "following", fill=(150, 150, 150), font=font_small)

    # Görseli byte dizisine çevir
    img_byte_arr = BytesIO()
    card.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

def check_instagram(username):
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
                pic_url = user_data.get("profile_pic_url_hd") or user_data.get("profile_pic_url")
                followers = user_data.get("edge_followed_by", {}).get("count", 0)
                following = user_data.get("edge_follow", {}).get("count", 0)
                posts = user_data.get("edge_owner_to_timeline_media", {}).get("count", 0)
                return "ACTIVE", pic_url, followers, following, posts
            else:
                return "CLOSED", None, 0, 0, 0
        elif response.status_code == 404:
            return "CLOSED", None, 0, 0, 0
        else:
            return "ACTIVE", None, 0, 0, 0
    except Exception as e:
        print(f"Instagram check error (@{username}): {e}")
        return "ERROR", None, 0, 0, 0

def process_telegram_commands():
    global last_update_id
    if not TELEGRAM_TOKEN:
        return
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
                
                if chat_id != str(CHAT_ID):
                    continue
                    
                if text.startswith("/unban"):
                    parts = text.split()
                    if len(parts) > 1:
                        username = parts[1].replace("@", "").strip()
                        unban_list.add(username)
                        if username in ban_list:
                            ban_list.remove(username)
                        send_telegram_message(f"👀 <b>Added to Unban Tracking:</b> @{username}\n(Waiting for account to open)")
                    else:
                        send_telegram_message("⚠️ Please specify a username. Example: /unban @username")
                        
                elif text.startswith("/ban"):
                    parts = text.split()
                    if len(parts) > 1:
                        username = parts[1].replace("@", "").strip()
                        ban_list.add(username)
                        if username in unban_list:
                            unban_list.remove(username)
                        send_telegram_message(f"👀 <b>Added to Ban Tracking:</b> @{username}\n(Waiting for account to close)")
                    else:
                        send_telegram_message("⚠️ Please specify a username. Example: /ban @username")
                        
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
                            send_telegram_message(f"🗑️ <b>Removed from tracking:</b> @{username}")
                        else:
                            send_telegram_message(f"⚠️ @{username} was not found in any tracking list.")
                    else:
                        send_telegram_message("⚠️ Please specify a username. Example: /remove @username")

                elif text.startswith("/list"):
                    msg_text = "📋 <b>Tracked Accounts:</b>\n\n"
                    msg_text += f"🟢 <b>Waiting for Unban:</b> {list(unban_list) if unban_list else 'Empty'}\n"
                    msg_text += f"🔴 <b>Waiting for Ban:</b> {list(ban_list) if ban_list else 'Empty'}"
                    send_telegram_message(msg_text)
    except Exception as e:
        print(f"Command processing error: {e}")

def main():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
    send_telegram_message("🚀 <b>Bot Updated with Custom Profile Cards!</b>")
    
    while True:
        try:
            process_telegram_commands()
            
            # Unban kontrolü
            current_unban = list(unban_list)
            for username in current_unban:
                if username not in unban_list:
                    continue
                process_telegram_commands()
                status, pic_url, followers, following, posts = check_instagram(username)
                if status == "ACTIVE":
                    formatted_followers = f"{followers:,}" if followers else "N/A"
                    caption = (
                        f"🧑‍👑 <b>Account Unbanned</b> 🧑‍👑\n"
                        f"👻 <b>Username:</b> @{username}\n"
                        f"👥 <b>Followers:</b> {formatted_followers}\n"
                        f"View Profile - @{username}"
                    )
                    if pic_url:
                        card_bytes = generate_profile_card(username, pic_url, posts, followers, following)
                        send_telegram_photo(card_bytes, caption)
                    else:
                        send_telegram_message(caption)
                    unban_list.discard(username)
                    
            # Ban kontrolü
            current_ban = list(ban_list)
            for username in current_ban:
                if username not in ban_list:
                    continue
                process_telegram_commands()
                status, pic_url, followers, following, posts = check_instagram(username)
                if status == "CLOSED":
                    formatted_followers = f"{followers:,}" if followers else "N/A"
                    caption = (
                        f"💀 <b>Account Banned</b> 💀\n"
                        f"👻 <b>Username:</b> @{username}\n"
                        f"👥 <b>Followers:</b> {formatted_followers}\n"
                        f"View Profile - @{username}"
                    )
                    if pic_url:
                        card_bytes = generate_profile_card(username, pic_url, posts, followers, following)
                        send_telegram_photo(card_bytes, caption)
                    else:
                        send_telegram_message(caption)
                    ban_list.discard(username)
                    
            time.sleep(15)
            
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
