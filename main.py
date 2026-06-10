import os
import re
import sqlite3
import threading
from flask import Flask
import telebot
from telebot import types

# ================= CONFIGURATION (সরাসরি এখানে পরিবর্তন করুন) =================
BOT_TOKEN = "8733427120:AAGlZgeJVkuKG_PxpQmM7YJpqgCHTC7OhOc"

# আপনার নিজের টেলিগ্রাম আইডি এখানে বসান (বটে /id কমান্ড দিয়ে আইডিটি পেয়ে যাবেন)
ADMIN_ID = 123456789  

# আপনার টেলিগ্রাম প্রাইভেট চ্যানেলের লিঙ্ক এখানে বসান
CHANNEL_LINK = "https://t.me/your_private_channel"  

# আপনার রেজিস্ট্রেশন লিঙ্ক
REGISTRATION_LINK = "https://tradexcope.com/r/Hc5qtsj1"

# আপনার সিগন্যাল ওয়েব অ্যাপ এর লিঙ্ক এখানে বসান
WEBAPP_LINK = "https://your-signal-webapp.com"  

# ব্যানার ইমেজ লিঙ্ক
IMAGE_URL = "https://i.ibb.co.com/Wvc0m3Dk/e79d43bd-a19f-4758-be61-ce6d3b9ea22c.png"
# ==============================================================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Admin state to keep track of broadcast
ADMIN_STATES = {}

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT,
            uid TEXT,
            status TEXT DEFAULT 'start',
            step TEXT DEFAULT 'start'
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(user_id, username):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def update_user(user_id, **kwargs):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

# --- HELPER PARSER FOR BROADCAST BUTTONS ---
def parse_broadcast_message(text):
    if not text:
        return "", None
    
    lines = text.split('\n')
    clean_lines = []
    buttons = []
    
    for line in lines:
        line_stripped = line.strip()
        match = re.search(r'\[?([^:\[\]]+?)[：:]\s*(https?://\S+)\]?$', line_stripped)
        if match:
            btn_text = match.group(1).strip()
            btn_url = match.group(2).strip()
            buttons.append((btn_text, btn_url))
        else:
            clean_lines.append(line)
            
    clean_text = "\n".join(clean_lines).strip()
    
    markup = None
    if buttons:
        markup = types.InlineKeyboardMarkup()
        for btn_text, btn_url in buttons:
            markup.add(types.InlineKeyboardButton(btn_text, url=btn_url))
            
    return clean_text, markup

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    add_user(user_id, username)
    
    user = get_user(user_id)
    if user and user[4] == "approved":
        send_approved_webapp(user_id)
        return

    update_user(user_id, step="join_channel")
    
    markup = types.InlineKeyboardMarkup()
    btn_join = types.InlineKeyboardButton("Join Telegram Channel", url=CHANNEL_LINK)
    btn_joined = types.InlineKeyboardButton("✅ Joined", callback_data="check_joined")
    markup.add(btn_join)
    markup.add(btn_joined)
    
    bot.send_message(
        user_id, 
        "👋 স্বাগতম! আমাদের বট ব্যবহার করতে প্রথমে আমাদের প্রাইভেট টেলিগ্রাম চ্যানেলে জয়েন করুন।\n\nWelcome! To use our bot, please join our private Telegram channel first.", 
        reply_markup=markup
    )

@bot.message_handler(commands=['id'])
def get_my_id(message):
    bot.reply_to(message, f"Your Telegram User ID is: `{message.from_user.id}`\n\nএই আইডিটি কপি করে কোডের `ADMIN_ID =` এর জায়গায় বসিয়ে দিন।", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "check_joined")
def check_joined_callback(call):
    user_id = call.from_user.id
    update_user(user_id, step="select_lang")
    
    markup = types.InlineKeyboardMarkup()
    btn_bn = types.InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn")
    btn_en = types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    markup.add(btn_bn, btn_en)
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text="👉 দয়া করে আপনার ভাষা নির্বাচন করুন।\n\n👉 Please select your language.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def lang_callback(call):
    user_id = call.from_user.id
    lang = "bn" if call.data == "lang_bn" else "en"
    update_user(user_id, language=lang, step="wait_uid")
    
    if lang == "bn":
        text = (
            f"📥 **ধাপ ২: রেজিস্ট্রেশন এবং ইউআইডি**\n\n"
            f"১. নিচের লিঙ্কে ক্লিক করে একটি নতুন অ্যাকাউন্ট তৈরি করুন:\n"
            f"🔗 {REGISTRATION_LINK}\n\n"
            f"২. অ্যাকাউন্ট তৈরি করার পর আপনার Trading UID (যেমন: 12345678) এখানে টেক্সট মেসেজ আকারে লিখে পাঠান।"
        )
    else:
        text = (
            f"📥 **Step 2: Registration & UID**\n\n"
            f"1. Click the link below to create a new account:\n"
            f"🔗 {REGISTRATION_LINK}\n\n"
            f"2. After creating the account, send your Trading UID (e.g., 12345678) here as a text message."
        )
        
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text=text,
        disable_web_page_preview=True,
        parse_mode="Markdown"
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    
    if user_id == ADMIN_ID and ADMIN_STATES.get(user_id) == "waiting_broadcast":
        process_broadcast(message)
        return

    user = get_user(user_id)
    if not user:
        return
        
    step = user[5]
    lang = user[2] or "en"
    
    if step == "wait_uid":
        uid_candidate = message.text.strip()
        
        if not uid_candidate.isdigit():
            if lang == "bn":
                bot.reply_to(message, "⚠️ ভুল UID! দয়া করে শুধুমাত্র সংখ্যায় আপনার UID পাঠান (যেমন: 12345678)।")
            else:
                bot.reply_to(message, "⚠️ Invalid UID! Please send numeric UID only (e.g., 12345678).")
            return
        
        update_user(user_id, uid=uid_candidate, status="pending", step="pending_approval")
        
        if lang == "bn":
            user_msg = (
                f"✅ আপনার UID ({uid_candidate}) গ্রহণ করা হয়েছে! ⏳\n\n"
                f"আপনার অ্যাকাউন্টটি একটিভ করতে এবং সিগন্যাল পেতে অনুগ্রহ করে এখনই এডমিনকে মেসেজ দিন:\n"
                f"👉 @TRADER_RAJ10\n\n"
                f"মেসেজে লিখবেন: 'আমার UID একটিভ করুন: {uid_candidate}'"
            )
        else:
            user_msg = (
                f"✅ Your UID ({uid_candidate}) has been received! ⏳\n\n"
                f"To activate your account and access signals, please message the Admin now:\n"
                f"👉 @TRADER_RAJ10\n\n"
                f"Write in message: 'Please activate my UID: {uid_candidate}'"
            )
            
        bot.send_message(user_id, user_msg)
        
        admin_notify_msg = (
            f"🔔 **নতুন UID সাবমিশন!**\n\n"
            f"👤 ইউজার: @{username}\n"
            f"🆔 টেলিগ্রাম আইডি: `{user_id}`\n"
            f"📈 Trading UID: `{uid_candidate}`\n\n"
            f"এই ইউজারকে অ্যাপ্রুভ করতে নিচের কমান্ডটি কপি করে পেস্ট করুন:\n"
            f"`/approve {user_id}`"
        )
        try:
            bot.send_message(ADMIN_ID, admin_notify_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Failed to notify admin: {e}")

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['approve'])
def approve_user(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "ব্যবহারবিধি: `/approve <user_id>`", parse_mode="Markdown")
            return
            
        target_user_id = int(parts[1])
        target_user = get_user(target_user_id)
        
        if not target_user:
            bot.reply_to(message, "ইউজার ডেটাবেজে খুঁজে পাওয়া যায়নি।")
            return
            
        update_user(target_user_id, status="approved", step="approved")
        send_approved_webapp(target_user_id)
        bot.reply_to(message, f"✅ ইউজার {target_user_id} সফলভাবে অ্যাপ্রুভ হয়েছে এবং নোটিফিকেশন পাঠানো হয়েছে।")
        
    except Exception as e:
        bot.reply_to(message, f"ত্রুটি: {e}")

def send_approved_webapp(user_id):
    caption = (
        "🚀 TRADER RAJ AI BOT\n"
        "⚡ Smart Signals • Fast Analysis • Maximum Accuracy\n"
        "📈 Trade Smarter, Earn Better"
    )
    markup = types.InlineKeyboardMarkup()
    btn_webapp = types.InlineKeyboardButton("Open Signal Webapp 📈", url=WEBAPP_LINK)
    markup.add(btn_webapp)
    
    try:
        bot.send_photo(
            chat_id=user_id,
            photo=IMAGE_URL,
            caption=caption,
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error sending photo to {user_id}: {e}")

# --- ADMIN BROADCAST MODE ---

@bot.message_handler(commands=['broadcast'])
def start_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    ADMIN_STATES[message.from_user.id] = "waiting_broadcast"
    bot.reply_to(
        message,
        "📢 **ব্রডকাস্ট মোড একটিভ হয়েছে**\n\n"
        "আপনার টেক্সট, ফটো বা ভিডিও পাঠান।\n\n"
        "যদি মেসেজে বাটন এড করতে চান তবে মেসেজের শেষে এভাবে লিখুন:\n"
        "`Button Text:https://yourlink.com`\n"
        "অথবা\n"
        "`[Button Text:https://yourlink.com]`\n\n"
        "বাতিল করতে `/cancel` লিখুন।",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['cancel'])
def cancel_action(message):
    if message.from_user.id != ADMIN_ID:
        return
    ADMIN_STATES[message.from_user.id] = None
    bot.reply_to(message, "❌ ব্রডকাস্ট বাতিল করা হয়েছে।")

@bot.message_handler(content_types=['photo', 'video'], func=lambda message: ADMIN_STATES.get(message.from_user.id) == "waiting_broadcast")
def process_broadcast_media(message):
    process_broadcast(message)

def process_broadcast(message):
    admin_id = message.from_user.id
    ADMIN_STATES[admin_id] = None
    
    text = message.text or message.caption or ""
    
    if text.strip() == "/cancel":
        bot.reply_to(message, "❌ ব্রডকাস্ট বাতিল করা হয়েছে।")
        return
        
    clean_text, markup = parse_broadcast_message(text)
    
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    all_users = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    bot.send_message(admin_id, f"📢 মোট {len(all_users)} ইউজারের কাছে ব্রডকাস্ট পাঠানো শুরু হয়েছে...")
    
    success_count = 0
    fail_count = 0
    
    for u_id in all_users:
        try:
            if message.content_type == 'text':
                bot.send_message(u_id, clean_text, reply_markup=markup, parse_mode="Markdown")
            elif message.content_type == 'photo':
                photo_file_id = message.photo[-1].file_id
                bot.send_photo(u_id, photo_file_id, caption=clean_text, reply_markup=markup, parse_mode="Markdown")
            elif message.content_type == 'video':
                video_file_id = message.video.file_id
                bot.send_video(u_id, video_file_id, caption=clean_text, reply_markup=markup, parse_mode="Markdown")
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Failed to send to {u_id}: {e}")
            
    bot.send_message(admin_id, f"📢 ব্রডকাস্ট সম্পন্ন হয়েছে!\n\n✅ সফল: {success_count}\n❌ ব্যর্থ: {fail_count}")

# --- WEB SERVER (For Render Keep Alive) ---
@app.route('/')
def index():
    return "Bot is successfully running!"

# --- STARTUP LOGIC ---
# ডেটাবেজ সেটআপ এবং ব্যাকগ্রাউন্ডে টেলিগ্রাম পোলিং চালু করা (Gunicorn দিয়ে রান করলেও এটি চলবে)
init_db()

def run_bot():
    print("Bot polling started...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot Polling Error: {e}")

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

# লোকাল টেস্ট করার জন্য (Render এ Gunicorn সরাসরি ‘app’ অবজেক্ট ব্যবহার করবে)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
