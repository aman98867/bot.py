import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests
import os
import threading
import json
from datetime import datetime
from flask import Flask

# ==========================================
# 🔑 YAHAN APNA TELEGRAM BOT TOKEN DALEIN
# ==========================================
BOT_TOKEN = "8705735671:AAGcSMXdZRsfHZQuTOiTFK679QtoWsLvdTs"

# 👑 YAHAN APNI TELEGRAM USER ID DALEIN (@userinfobot se nikal kar)
ADMIN_ID = 7870416602  

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# 🌐 24*7 KEEP ALIVE SYSTEM (FLASK)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Jio Gemini Bot is Alive and Running 24/7!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_server, daemon=True).start()

# ==========================================
# ⚙️ API HEADERS & CONFIG
# ==========================================
BASE_URL = "https://looters.shop/jio_gemini/"
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Origin": "https://looters.shop",
    "Referer": "https://looters.shop/jio_gemini/",
}

user_state = {}
DB_FILE = "users_db.json" # Advanced JSON Database

# ==========================================
# 👥 ADVANCED DATABASE SYSTEM
# ==========================================
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)

def track_user(message):
    db = load_db()
    user_id = str(message.from_user.id)
    
    # Agar naya user hai, toh uska poora data save karo
    if user_id not in db:
        db[user_id] = {
            "name": message.from_user.first_name or "Unknown",
            "username": message.from_user.username or "None",
            "links_generated": 0,
            "joined": datetime.now().strftime("%Y-%m-%d")
        }
        save_db(db)
    else:
        # Update name/username if changed
        db[user_id]["name"] = message.from_user.first_name or "Unknown"
        db[user_id]["username"] = message.from_user.username or "None"
        save_db(db)

def add_link_count(user_id):
    db = load_db()
    uid = str(user_id)
    if uid in db:
        db[uid]["links_generated"] += 1
        save_db(db)

# ==========================================
# 🎛️ BOTTOM MENU BUTTONS
# ==========================================
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("🚀 Generate Link")
    btn2 = KeyboardButton("👤 My Profile")
    markup.add(btn1, btn2)
    return markup

# ==========================================
# 👑 ADMIN PANEL COMMANDS
# ==========================================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.reply_to(message, "❌ Aap admin nahi hain! Yeh command aapke liye nahi hai.")
        return
    
    text = (
        "👑 **VIP ADMIN PANEL** 👑\n\n"
        "📊 `/stats` - Total users & overall links dekhein\n"
        "👥 `/users` - User ki details aur history dekhein\n"
        "📢 `/broadcast <message>` - Sabko message bhejein"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.chat.id != ADMIN_ID:
        return
    
    db = load_db()
    total_users = len(db)
    total_links = sum(user["links_generated"] for user in db.values())
    
    text = (
        "📊 **BOT STATISTICS** 📊\n\n"
        f"👥 **Total Unique Users:** `{total_users}`\n"
        f"🔗 **Total Links Generated:** `{total_links}`"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.chat.id != ADMIN_ID:
        return
    
    db = load_db()
    if not db:
        bot.reply_to(message, "❌ Abhi tak kisi ne bot use nahi kiya hai.")
        return
        
    text = "👥 **USER DATABASE:**\n\n"
    for uid, info in db.items():
        uname = f"@{info['username']}" if info['username'] != "None" else "No Username"
        text += f"👤 **Name:** {info['name']} ({uname})\n"
        text += f"🆔 **ID:** `{uid}`\n"
        text += f"🔗 **Links Generated:** `{info['links_generated']}`\n"
        text += "〰️〰️〰️〰️〰️〰️〰️〰️\n"
        
    # Telegram message length limit handle karna (agar user zyada ho jayein)
    if len(text) > 4000:
        with open("user_list.txt", "w", encoding="utf-8") as f:
            f.write(text.replace("*", "").replace("`", "")) # Markdown hata ke txt banaya
        with open("user_list.txt", "rb") as doc:
            bot.send_document(message.chat.id, doc, caption="📁 Users ki list bahut badi thi, isliye file bhej di gayi hai.")
        os.remove("user_list.txt")
    else:
        bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.chat.id != ADMIN_ID:
        return
    
    msg_text = message.text.replace("/broadcast", "").strip()
    if not msg_text:
        bot.reply_to(message, "⚠️ Sahi Format: `/broadcast Aapka message yahan`", parse_mode="Markdown")
        return

    db = load_db()
    if not db:
        bot.reply_to(message, "❌ Koi user nahi mila database mein.")
        return

    bot.reply_to(message, "⏳ Broadcast shuru ho gaya hai...")
    success = 0
    for user_id in db.keys():
        try:
            bot.send_message(user_id, f"📢 **Admin Message:**\n\n{msg_text}", parse_mode="Markdown")
            success += 1
        except Exception:
            pass 
    
    bot.reply_to(message, f"✅ **Broadcast Complete!**\n📨 Sent successfully to: `{success}/{len(db)}` users.", parse_mode="Markdown")

# ==========================================
# 🚀 BOT COMMANDS & SMART DETECTION
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    track_user(message) # User ka data JSON mein save
    
    text = (
        "🌟 **Jio Gemini Pro Bot** mein aapka swagat hai!\n\n"
        "👇 Niche diye gaye Buttons ka use karein, ya direct apna **Number** bhejein."
    )
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id
    
    track_user(message) # Track user interaction

    # 1. Button: Generate Link
    if text == "🚀 Generate Link":
        bot.reply_to(message, "📱 Apna 10-digit Jio number bhejein:", reply_markup=main_menu())
        
    # 2. Button: My Profile
    elif text == "👤 My Profile":
        db = load_db()
        info = db.get(str(chat_id), {})
        count = info.get("links_generated", 0)
        joined = info.get("joined", "Unknown")
        
        profile_text = (
            f"👤 **Aapki Profile**\n\n"
            f"🆔 **ID:** `{chat_id}`\n"
            f"🔗 **Links Generated:** `{count}`\n"
            f"📅 **Joined on:** `{joined}`"
        )
        bot.reply_to(message, profile_text, parse_mode="Markdown")
        
    # 3. Smart Detect: 10-Digit Number
    elif text.isdigit() and len(text) == 10:
        bot.reply_to(message, f"⏳ {text} par OTP bheja ja raha hai...")
        
        user_session = requests.Session()
        try:
            res = user_session.post(BASE_URL, data={"action": "send_otp", "number": text}, headers=API_HEADERS, timeout=20)
            data = res.json()
            
            if data.get("success"):
                user_state[chat_id] = {"step": "waiting_for_otp", "number": text, "session": user_session}
                bot.reply_to(message, "✅ OTP bhej diya gaya! Kripya 6-digit OTP bhejein:")
            else:
                bot.reply_to(message, f"❌ OTP nahi gaya: {data.get('message')}")
        except Exception:
            bot.reply_to(message, "⚠️ Server down hai, baad mein try karein.")

    # 4. Smart Detect: 6-Digit OTP
    elif text.isdigit() and len(text) == 6:
        state = user_state.get(chat_id, {})
        if state.get("step") == "waiting_for_otp":
            number = state.get("number")
            user_session = state.get("session")
            
            bot.reply_to(message, "⏳ OTP verify ho raha hai...")
            try:
                res = user_session.post(BASE_URL, data={"action": "verify_otp", "number": number, "otp": text}, headers=API_HEADERS, timeout=60)
                data = res.json()
                
                if data.get("success"):
                    link = data.get("link", "Link not found")
                    
                    bot.reply_to(message, "🎉 **BOOM! Link ban gaya!** 🎉\n👇 Yahan se copy karein:", parse_mode="Markdown")
                    bot.send_message(chat_id, link, reply_markup=main_menu()) 
                    
                    add_link_count(chat_id) # 🟢 Success par user ka score +1 kar do
                    user_state.pop(chat_id, None)
                else:
                    bot.reply_to(message, f"❌ Fail ho gaya: {data.get('message')}")
            except Exception:
                bot.reply_to(message, "⚠️ Server bahut time le raha hai.")
        else:
            bot.reply_to(message, "❌ Pehle ek 10-digit number daalkar OTP mangwayein!")

    # 5. Agar kuch aur ulta seedha likha ho
    else:
        bot.reply_to(message, "🤔 Kuch samajh nahi aaya. Niche diye gaye buttons use karein, ya direct 10-digit Number bhejein.", reply_markup=main_menu())

# ==========================================
# 🏃‍♂️ START BOT
# ==========================================
if __name__ == "__main__":
    print("🚀 Smart Admin Bot is running...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
