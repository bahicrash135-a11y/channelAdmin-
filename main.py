import os
import json
import threading
import urllib.parse
from flask import Flask
import telebot
from telebot import types

# Render-এর পোর্ট বাইন্ডিংয়ের জন্য Flask অ্যাপ তৈরি
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running online with Colored Buttons!"

@app.route('/health')
def health():
    return "OK", 200

# আপনার দেওয়া টোকেন এবং এডমিন ইউজারনেম
TOKEN = "8338804278:AAGAIJE02dT8zW7vX35ynlqPpcmoxjBe_bs"
ADMIN_USERNAME = "TRADER_RAJ10"

bot = telebot.TeleBot(TOKEN)
CHANNELS_FILE = "channels.json"

# চ্যানেল ডাটাবেজ লোড করার ফাংশন
def load_channels():
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# channel ডাটাবেজ সেভ করার ফাংশন
def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

# সাময়িকভাবে পোস্টের তথ্য রাখার জন্য ডিকশনারি
user_data = {}

# ইউআরএল বা লিংক ভ্যালিডেশন চেক করার ফাংশন
def is_valid_url(url):
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

# এডমিন কিনা তা যাচাই করার ফাংশন
def is_admin(message):
    username = message.from_user.username
    if username and username.lower() == ADMIN_USERNAME.lower():
        return True
    
    # ইউজার এডমিন না হলে তাকে তার ইউজারনেমসহ এরর মেসেজ দেখাবে (ডিবাগিংয়ের সুবিধার জন্য)
    display_username = f"@{username}" if username else "ইউজারনেম সেট করা নেই"
    bot.reply_to(message, f"❌ দুঃখিত, আপনি এই বটের এডমিন নন।\n👤 আপনার ইউজারনেম: {display_username}\n⚙️ অনুমতিপ্রাপ্ত এডমিন ইউজারনেম: @{ADMIN_USERNAME}")
    return False

# /start বা /help কমান্ড
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_admin(message): 
        return
    
    help_text = (
        "👋 **স্বাগতম!** এটি আপনার পোস্ট কন্ট্রোলার বট।\n\n"
        "📌 **এডমিন কমান্ডসমূহ:**\n"
        "🔹 `/addchannel <চ্যানেল ইউজারনেম বা আইডি>` - নতুন চ্যানেল যুক্ত করুন।\n"
        "🔹 `/removechannel <চ্যানেল ইউজারনেম বা আইডি>` - চ্যানেল তালিকা থেকে সরিয়ে দিন।\n"
        "🔹 `/listchannels` - যুক্ত থাকা সকল চ্যানেলের তালিকা দেখুন।\n"
        "🔹 `/createpost` - বাটনসহ নতুন পোস্ট তৈরি ও পাবলিশ করুন।\n\n"
        "⚠️ **গুরুত্বপূর্ণ নোট:** পোস্ট সফলভাবে পাঠানোর জন্য বটটিকে অবশ্যই আপনার টার্গেট চ্যানেলে 'Administrator' হিসেবে যুক্ত করতে হবে এবং পোস্ট করার অনুমতি (Post Messages permission) দিতে হবে।"
    )
    bot.reply_to(message, help_text, parse_mode="HTML")

# নতুন চ্যানেল যুক্ত করার কমান্ড
@bot.message_handler(commands=['addchannel'])
def add_channel(message):
    if not is_admin(message): 
        return
    
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ ব্যবহার নিয়ম:\n`/addchannel @channel_username` (পাবলিক চ্যানেলের জন্য)\nঅথবা\n`/addchannel -100123456789` (প্রাইভেট চ্যানেলের আইডির জন্য)", parse_mode="Markdown")
            return
        
        new_channel = parts[1].strip()
        channels = load_channels()
        
        if new_channel not in channels:
            channels.append(new_channel)
            save_channels(channels)
            bot.reply_to(message, f"✅ চ্যানেল `{new_channel}` সফলভাবে যুক্ত করা হয়েছে।\n(নিশ্চিত করুন বটটি এই চ্যানেলের এডমিন হিসেবে যুক্ত আছে।)", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ এই চ্যানেলটি ইতিমধ্যেই আপনার তালিকায় যুক্ত আছে।")
    except Exception as e:
        bot.reply_to(message, f"❌ ত্রুটি ঘটেছে: {str(e)}")

# চ্যানেল মুছে ফেলার কমান্ড
@bot.message_handler(commands=['removechannel'])
def remove_channel(message):
    if not is_admin(message): 
        return
    
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ ব্যবহার নিয়ম: `/removechannel @channel_username` অথবা `/removechannel -100123456789`", parse_mode="Markdown")
            return
        
        target_channel = parts[1].strip()
        channels = load_channels()
        
        if target_channel in channels:
            channels.remove(target_channel)
            save_channels(channels)
            bot.reply_to(message, f"✅ চ্যানেল `{target_channel}` তালিকা থেকে সরিয়ে দেওয়া হয়েছে।", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ এই চ্যানেলটি তালিকায় পাওয়া যায়নি।")
    except Exception as e:
        bot.reply_to(message, f"❌ ত্রুটি ঘটেছে: {str(e)}")

# চ্যানেলের তালিকা দেখার কমান্ড
@bot.message_handler(commands=['listchannels'])
def list_channels(message):
    if not is_admin(message): 
        return
    
    channels = load_channels()
    if not channels:
        bot.reply_to(message, "📂 কোনো চ্যানেল যুক্ত করা নেই।")
    else:
        text = "📋 **আপনার যুক্তকৃত চ্যানেলের তালিকা:**\n\n"
        for i, ch in enumerate(channels, 1):
            text += f"{i}. `{ch}`\n"
        bot.reply_to(message, text, parse_mode="Markdown")

# নতুন পোস্ট তৈরি করার ধাপ ১: পোস্ট কন্টেন্ট গ্রহণ
@bot.message_handler(commands=['createpost'])
def start_post(message):
    if not is_admin(message): 
        return
    
    msg = bot.reply_to(message, "📝 আপনার পোস্টটি পাঠান।\n(আপনি সাধারণ টেক্সট, ফটো বা ভিডিও পাঠাতে পারেন):")
    bot.register_next_step_handler(msg, process_post_content)

# পোস্ট তৈরি করার ধাপ ২: কন্টেন্ট প্রসেস এবং টাইটেল বা বিবরণ চাওয়া
def process_post_content(message):
    chat_id = message.chat.id
    content_type = message.content_type
    
    user_data[chat_id] = {
        'text': message.text or message.caption or "",
        'photo': message.photo[-1].file_id if message.photo else None,
        'video': message.video.file_id if message.video else None,
        'content_type': content_type
    }
    
    # যদি ফটো বা ভিডিও পাঠানো হয়, তবে টাইটেল বা বিবরণ সেট করার নতুন ধাপ
    if content_type in ['photo', 'video']:
        msg = bot.send_message(
            chat_id, 
            "📝 আপনার ফটো বা ভিডিওর জন্য একটি টাইটেল বা বিবরণ (Caption) পাঠান।\n"
            "(কোনো টাইটেল বা ক্যাপশন দিতে না চাইলে অথবা আগের ক্যাপশনটিই রাখতে চাইলে 'skip' লিখে পাঠান):"
        )
        bot.register_next_step_handler(msg, process_post_title)
    else:
        # টেক্সট পোস্ট হলে সরাসরি বাটন সেট করার অপশনে চলে যাবে
        ask_for_buttons(chat_id)

# পোস্ট তৈরি করার ধাপ ২.৫: টাইটেল/ক্যাপশন ইনপুট নেওয়া (ফটো বা ভিডিওর জন্য)
def process_post_title(message):
    chat_id = message.chat.id
    title_text = message.text.strip() if message.text else ""
    
    # ইউজার 'skip' না লিখলে তার পাঠানো টেক্সটটিকে টাইটেল বা ক্যাপশন হিসেবে সেট করা হবে
    if title_text and title_text.lower() != 'skip':
        user_data[chat_id]['text'] = message.text
        
    ask_for_buttons(chat_id)

# বাটন ইনপুট নেওয়ার জন্য নির্দেশনা পাঠানো
def ask_for_buttons(chat_id):
    msg = bot.send_message(
        chat_id, 
        "🔗 এবার নিচে বাটন, লিংক এবং কালার যুক্ত করুন।\n\n"
        "**ফরমেট:**\n"
        "`বাটন নাম | লিংক | কালার`\n\n"
        "**কালার অপশনসমূহ:**\n"
        "🔴 `red` (লাল)\n"
        "🟢 `green` (সবুজ)\n"
        "🔵 `blue` (নীল)\n"
        "⚪ `white` (সাদা)\n\n"
        "**উদাহরণ:**\n"
        "`ইউটিউব চ্যানেল | https://youtube.com | red`\n"
        "`গ্রুপে জয়েন করুন | https://t.me/TRADER_RAJ10 | green`\n\n"
        "💡 *কালার না দিতে চাইলে শুধু নাম ও লিংক দিলেই হবে (ডিফল্ট কালার পাবে)। কোনো বাটন না চাইলে 'skip' লিখে পাঠান।*",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_post_buttons)

# পোস্ট তৈরি করার ধাপ ৩: বাটন প্রসেস ও চ্যানেল সিলেক্ট
def process_post_buttons(message):
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""
    
    buttons = []
    if text.lower() != 'skip':
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    btn_text = parts[0].strip()
                    btn_url = parts[1].strip()
                    
                    # লিংকে স্কিম (https://) না থাকলে স্বয়ংক্রিয়ভাবে যোগ করা
                    if not (btn_url.startswith('http://') or btn_url.startswith('https://')):
                        btn_url = 'https://' + btn_url
                    
                    btn_style = None
                    if len(parts) >= 3:
                        color_input = parts[2].strip().lower()
                        if color_input in ['red', 'danger', 'r']:
                            btn_style = 'danger'
                            btn_text = "🔴 " + btn_text
                        elif color_input in ['green', 'success', 'g']:
                            btn_style = 'success'
                            btn_text = "🟢 " + btn_text
                        elif color_input in ['blue', 'primary', 'b']:
                            btn_style = 'primary'
                            btn_text = "🔵 " + btn_text
                        elif color_input in ['white', 'w']:
                            btn_text = "⚪ " + btn_text
                            
                    if is_valid_url(btn_url):
                        buttons.append({'text': btn_text, 'url': btn_url, 'style': btn_style})
    
    user_data[chat_id]['buttons'] = buttons
    
    channels = load_channels()
    if not channels:
        bot.send_message(chat_id, "❌ কোনো চ্যানেল যুক্ত করা নেই। অনুগ্রহ করে প্রথমে `/addchannel` ব্যবহার করে চ্যানেল যুক্ত করুন।")
        return
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        markup.add(types.InlineKeyboardButton(text=f"📢 {ch}", callback_data=f"send_to:{ch}"))
    markup.add(types.InlineKeyboardButton(text="📢 সকল চ্যানেলে পাঠান (Send to All)", callback_data="send_to:all"))
    markup.add(types.InlineKeyboardButton(text="❌ বাতিল করুন (Cancel)", callback_data="cancel_post"))
    
    bot.send_message(chat_id, "🎯 আপনি পোস্টটি কোন চ্যানেলে পাঠাতে চান? নিচের অপশন থেকে নির্বাচন করুন:", reply_markup=markup)

# বাটন ক্লিক হ্যান্ডলার (পোস্ট পাঠানো বা বাতিল করা)
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    
    if call.data.startswith("send_to:"):
        target = call.data.replace("send_to:", "")
        post_info = user_data.get(chat_id)
        
        if not post_info:
            bot.answer_callback_query(call.id, "❌ পোস্টের তথ্য পাওয়া যায়নি। নতুন করে চেষ্টা করুন।")
            return
            
        channels = load_channels()
        targets_to_send = channels if target == "all" else [target]
        
        post_markup = types.InlineKeyboardMarkup()
        for btn in post_info.get('buttons', []):
            try:
                # TeleBot-এর নতুন ভার্সন অনুযায়ী কালার বাটন স্টাইল যোগ করা হচ্ছে
                post_markup.add(types.InlineKeyboardButton(
                    text=btn['text'], 
                    url=btn['url'], 
                    style=btn.get('style')
                ))
            except TypeError:
                # যদি কোনো কারণে সার্ভারের পাইথন লাইব্রেরি পুরোনো হয়, তবে সাধারণ বাটন তৈরি করবে
                post_markup.add(types.InlineKeyboardButton(
                    text=btn['text'], 
                    url=btn['url']
                ))
            except Exception:
                continue
            
        success_count = 0
        fail_count = 0
        error_logs = []
        
        for ch in targets_to_send:
            try:
                # Markdown জটিলতা এড়াতে সাধারণ ফরম্যাটে পাঠানো হচ্ছে
                if post_info['content_type'] == 'text':
                    bot.send_message(ch, post_info['text'], reply_markup=post_markup)
                elif post_info['content_type'] == 'photo':
                    bot.send_photo(ch, post_info['photo'], caption=post_info['text'], reply_markup=post_markup)
                elif post_info['content_type'] == 'video':
                    bot.send_video(ch, post_info['video'], caption=post_info['text'], reply_markup=post_markup)
                    success_count += 1
            except Exception as e:
                fail_count += 1
                error_logs.append(f"❌ `{ch}`: {str(e)}")
        
        result_message = (
            f"✅ **পোস্টের প্রক্রিয়া সম্পন্ন হয়েছে!**\n\n"
            f"🎉 সফলভাবে প্রেরিত: `{success_count}` টি চ্যানেল\n"
            f"❌ ব্যর্থ হয়েছে: `{fail_count}` টি চ্যানেল\n"
        )
        
        if error_logs:
            result_message += "\n📋 **ব্যর্থ হওয়ার সুনির্দিষ্ট কারণসমূহ নিচে দেওয়া হলো:**\n" + "\n".join(error_logs)
            
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=result_message,
            parse_mode="Markdown"
        )
        user_data.pop(chat_id, None)
        
    elif call.data == "cancel_post":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="❌ পোস্ট পাঠানো বাতিল করা হয়েছে।")
        user_data.pop(chat_id, None)


# ==========================================
# GUNICORN এবং RENDER এর জন্য গ্লোবাল স্টার্টআপ সেটিংস
# ==========================================

# টেলিগ্রাম পোলিং চালু করার মূল ফাংশন
def start_bot_polling():
    try:
        print("Webhook রিমুভ করা হচ্ছে...")
        bot.remove_webhook()
        print("টেলিগ্রাম বট পোলিং সফলভাবে চালু করা হচ্ছে...")
        # skip_pending=True দেওয়ার ফলে অফলাইনে থাকা অবস্থায় জমা হওয়া পুরানো মেসেজগুলো স্কিপ হবে
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"বট পোলিং চালুর সময় ত্রুটি ঘটেছে: {e}")

# Gunicorn যাতে ইমপোর্ট করার সাথে সাথে ব্যাকগ্রাউন্ডে বট চালু করতে পারে
bot_thread = threading.Thread(target=start_bot_polling)
bot_thread.daemon = True
bot_thread.start()

# Render-এর লোকাল ডেভেলপমেন্ট এবং পোর্ট বাইন্ডিং
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
