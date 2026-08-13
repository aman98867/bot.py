import telebot
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

# Server ko background mein chalayein
threading.Thread(target=run_server, daemon=True).start()

# ==========================================
# ⚙️ API HEADERS
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

# Ab hum har user ka 'number' aur ek personal 'session' save karenge
user_data = {} 

# ==========================================
# 🚀 BOT COMMANDS
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🌟 **Jio Gemini Pro Bot** mein aapka swagat hai!\n\n"
        "👇 Neeche diye gaye commands par click karein:\n\n"
        "🚀 /gen - Naya link banane ke liye\n"
        "⚡ /check - Link check karne ke liye"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

# ----------------- 🔍 CHECKER -----------------
@bot.message_handler(commands=['check'])
def ask_check_url(message):
    msg = bot.reply_to(message, "🔗 Koi Google One ka link bhejein:")
    bot.register_next_step_handler(msg, process_check_url)

def process_check_url(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Yeh link nahi hai! Phir se /check dabayein.")
        return

    bot.reply_to(message, "⏳ Checking chalu hai, thoda wait karein...")
    
    try:
        response = requests.get(url, headers=CHECK_HEADERS, timeout=15)
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
        bot.reply_to(message, "❌ Network mein koi issue hai.")

# ----------------- 🚀 GENERATOR -----------------
@bot.message_handler(commands=['gen'])
def ask_number(message):
    msg = bot.reply_to(message, "📱 Apna 10-digit Jio number dein:")
    bot.register_next_step_handler(msg, process_number)

def process_number(message):
    number = message.text.strip()
    if not (number.isdigit() and len(number) == 10):
        bot.reply_to(message, "❌ Number galat hai! Phir se /gen dabayein.")
        return

    bot.reply_to(message, f"⏳ {number} par OTP bheja ja raha hai...")
    
    # Naya session banayenge taaki OTP bhejte aur verify karte time same session rahe
    user_session = requests.Session()
    
    try:
        res = user_session.post(BASE_URL, data={"action": "send_otp", "number": number}, headers=API_HEADERS, timeout=20)
        data = res.json()
        if data.get("success"):
            # Number aur Session dono ko save kar liya
            user_data[message.chat.id] = {"number": number, "session": user_session}
            
            msg = bot.reply_to(message, "✅ OTP bhej diya gaya! Kripya 6-digit OTP bhejein:")
            bot.register_next_step_handler(msg, process_otp)
        else:
            bot.reply_to(message, f"❌ OTP nahi gaya: {data.get('message')}")
    except Exception:
        bot.reply_to(message, "⚠️ Server down hai, baad mein try karein.")

def process_otp(message):
    otp = message.text.strip()
    chat_id = message.chat.id
    
    if not (otp.isdigit() and len(otp) == 6):
        bot.reply_to(message, "❌ OTP 6 digit ka hona chahiye! Phir se /gen se shuru karein.")
        return

    # User ka number aur wahi purana session waapas nikalenge
    user_info = user_data.get(chat_id, {})
    number = user_info.get("number")
    user_session = user_info.get("session")
    
    if not number or not user_session:
        bot.reply_to(message, "❌ Session expire ho gaya ya number nahi mila, phir se /gen dabayein.")
        return

    bot.reply_to(message, "⏳ OTP check ho raha hai, link generate ho raha hai...")

    try:
        # Same user_session ka istemaal karke OTP verify karenge
        res = user_session.post(BASE_URL, data={"action": "verify_otp", "number": number, "otp": otp}, headers=API_HEADERS, timeout=60)
        data = res.json()
        if data.get("success"):
            link = data.get("link", "Link not found")
            bot.reply_to(message, f"🎉 **BOOM! Link ban gaya!** 🎉\n\n🔗 {link}", parse_mode="Markdown")
            
            # Kaam hone ke baad memory se data hata do taaki safai rahe
            user_data.pop(chat_id, None)
        else:
            bot.reply_to(message, f"❌ Fail ho gaya: {data.get('message')}")
    except Exception:
        bot.reply_to(message, "⚠️ Server bahut time le raha hai.")

# ==========================================
# 🏃‍♂️ START BOT
# ==========================================
print("🚀 Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
