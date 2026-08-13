import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests
import os
import threading
from flask import Flask

# ==========================================
# 🔑 YAHAN APNA TELEGRAM BOT TOKEN DALEIN
# ==========================================
BOT_TOKEN = "8705735671:AAGcSMXdZRsfHZQuTOiTFK679QtoWsLvdTs"
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
CHECK_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0 Safari/537.36'
}

# Har user ka data aur unka current "step" (jaise waiting for OTP) save karne ke liye
user_state = {}

# ==========================================
# 🎛️ BOTTOM MENU BUTTONS
# ==========================================
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("🚀 Generate Link")
    btn2 = KeyboardButton("⚡ Check Link")
    markup.add(btn1, btn2)
    return markup

# ==========================================
# 🚀 BOT COMMANDS & SMART DETECTION
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🌟 **Jio Gemini Pro Bot** mein aapka swagat hai!\n\n"
        "Ab commands ki zaroorat nahi!\n"
        "👇 Niche diye gaye Buttons ka use karein, ya direct apna **Number** ya **Link** bhejein."
    )
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=main_menu())

# Sab kuch ek hi jagah handle hoga (Smart Detection)
@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id

    # 1. Button: Generate Link
    if text == "🚀 Generate Link":
        bot.reply_to(message, "📱 Apna 10-digit Jio number bhejein:", reply_markup=main_menu())
        
    # 2. Button: Check Link
    elif text == "⚡ Check Link":
        bot.reply_to(message, "🔗 Apna Google One link paste karein:", reply_markup=main_menu())
        
    # 3. Smart Detect: 10-Digit Number (Direct OTP Bhejna)
    elif text.isdigit() and len(text) == 10:
        bot.reply_to(message, f"⏳ {text} par OTP bheja ja raha hai...")
        
        user_session = requests.Session()
        try:
            res = user_session.post(BASE_URL, data={"action": "send_otp", "number": text}, headers=API_HEADERS, timeout=20)
            data = res.json()
            
            if data.get("success"):
                # State save kar li ki ab is user se OTP chahiye
                user_state[chat_id] = {"step": "waiting_for_otp", "number": text, "session": user_session}
                bot.reply_to(message, "✅ OTP bhej diya gaya! Kripya 6-digit OTP bhejein:")
            else:
                bot.reply_to(message, f"❌ OTP nahi gaya: {data.get('message')}")
        except Exception:
            bot.reply_to(message, "⚠️ Server down hai, baad mein try karein.")

    # 4. Smart Detect: 6-Digit OTP (Verify aur Link Generate)
    elif text.isdigit() and len(text) == 6:
        # Check karenge ki kya user ka OTP wait ho raha tha
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
                    
                    # Kaam khatam, state clear kar do
                    user_state.pop(chat_id, None)
                else:
                    bot.reply_to(message, f"❌ Fail ho gaya: {data.get('message')}")
            except Exception:
                bot.reply_to(message, "⚠️ Server bahut time le raha hai.")
        else:
            bot.reply_to(message, "❌ Pehle ek 10-digit number daalkar OTP mangwayein!")

    # 5. Smart Detect: Link Checker
    elif text.startswith("http"):
        bot.reply_to(message, "⏳ Link check ho raha hai...")
        try:
            response = requests.get(text, headers=CHECK_HEADERS, timeout=15)
            if response.status_code == 200:
                used_keywords = ["already been used", "already redeemed", "has been used", "offer limit reached"]
                if any(kw in response.text.lower() for kw in used_keywords):
                    bot.reply_to(message, "⚠️ **USED:** Link open ho raha hai, par code pehle hi USED ho chuka hai!", parse_mode="Markdown")
                else:
                    bot.reply_to(message, "✅ **FRESH (WORKING):** Link ekdum sahi hai! (Status: 200 OK)", parse_mode="Markdown")
            elif response.status_code == 404:
                bot.reply_to(message, "❌ **NOT FOUND:** Ye link exist nahi karta.")
            else:
                bot.reply_to(message, f"⚠️ **ERROR:** Link mein issue hai. (Status: {response.status_code})")
        except Exception:
            bot.reply_to(message, "❌ Network ya link mein koi issue hai.")
            
    # 6. Agar kuch aur ulta seedha likha ho
    else:
        bot.reply_to(message, "🤔 Kuch samajh nahi aaya. Niche diye gaye buttons use karein, ya direct Number/Link bhejein.", reply_markup=main_menu())

# ==========================================
# 🏃‍♂️ START BOT
# ==========================================
if __name__ == "__main__":
    print("🚀 Smart Bot is running...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
