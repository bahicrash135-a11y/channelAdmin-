import telebot
from telebot import types
import json
import os

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

# চ্যানেল ডাটাবেজ সেভ করার ফাংশন
def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

# সাময়িকভাবে পোস্টের তথ্য রাখার জন্য ডিকশনারি
user_data = {}

# এডমিন কিনা তা যাচাই করার ফাংশন
def is_admin(message):
    username = message.from_user.username
    if username and username.lower() == ADMIN_USERNAME.lower():
        return True
    bot.reply_to(message, "❌ দুঃখিত, আপনি এই বটের এডমিন নন।")
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
    bot.reply_to(message, help_text, parse_mode="Markdown")

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

# নতুন পোস্ট তৈরি করার ধাপ ১: পোস্ট গ্রহণ
@bot.message_handler(commands=['createpost'])
def start_post(message):
    if not is_admin(message): 
        return
    
    msg = bot.reply_to(message, "📝 আপনার পোস্টটি পাঠান।\n(আপনি সাধারণ টেক্সট, ফটো অথবা ভিডিও পাঠাতে পারেন):")
    bot.register_next_step_handler(msg, process_post_content)

# পোস্ট তৈরি করার ধাপ ২: কন্টেন্ট প্রসেস এবং বাটন চাওয়া
def process_post_content(message):
    chat_id = message.chat.id
    user_data[chat_id] = {
        'text': message.text or message.caption or "",
        'photo': message.photo[-1].file_id if message.photo else None,
        'video': message.video.file_id if message.video else None,
        'content_type': message.content_type
    }
    
    msg = bot.send_message(
        chat_id, 
        "🔗 এবার নিচে বাটন এবং লিংক যুক্ত করুন।\n\n"
        "**ফরমেট:**\n"
        "`বাটন নাম | https://link1.com`\n"
        "`বাটন নাম ২ | https://link2.com`\n\n"
        "💡 *একাধিক বাটন নিচে নিচে দিতে পারেন। কোনো বাটন যুক্ত করতে না চাইলে 'skip' লিখে পাঠান।*",
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
                btn_text = parts[0].strip()
                btn_url = parts[1].strip()
                buttons.append({'text': btn_text, 'url': btn_url})
    
    user_data[chat_id]['buttons'] = buttons
    
    channels = load_channels()
    if not channels:
        bot.send_message(chat_id, "❌ কোনো চ্যানেল যুক্ত করা নেই। অনুগ্রহ করে প্রথমে `/addchannel` ব্যবহার করে চ্যানেল যুক্ত করুন।", parse_mode="Markdown")
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
        
        # বাটন লেআউট তৈরি
        post_markup = types.InlineKeyboardMarkup()
        for btn in post_info.get('buttons', []):
            try:
                post_markup.add(types.InlineKeyboardButton(text=btn['text'], url=btn['url']))
            except Exception:
                continue  # ভুল লিংকের কারণে ক্রাশ হওয়া প্রতিরোধ করতে
            
        success_count = 0
        fail_count = 0
        
        # পোস্ট পাঠানো শুরু
        for ch in targets_to_send:
            try:
                if post_info['content_type'] == 'text':
                    bot.send_message(ch, post_info['text'], reply_markup=post_markup, parse_mode="Markdown")
                elif post_info['content_type'] == 'photo':
                    bot.send_photo(ch, post_info['photo'], caption=post_info['text'], reply_markup=post_markup, parse_mode="Markdown")
                elif post_info['content_type'] == 'video':
                    bot.send_video(ch, post_info['video'], caption=post_info['text'], reply_markup=post_markup, parse_mode="Markdown")
                success_count += 1
            except Exception as e:
                print(f"Error sending to {ch}: {e}")
                fail_count += 1
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"✅ **পোস্টের প্রক্রিয়া সম্পন্ন হয়েছে!**\n\n🎉 সফলভাবে প্রেরিত: `{success_count}` টি চ্যানেল\n❌ ব্যর্থ হয়েছে: `{fail_count}` টি চ্যানেল\n\n*(ব্যর্থ হওয়ার সম্ভাব্য কারণ: বটের কাছে চ্যানেলে পোস্ট করার এডমিন পারমিশন নেই)*",
            parse_mode="Markdown"
        )
        user_data.pop(chat_id, None)
        
    elif call.data == "cancel_post":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="❌ পোস্ট পাঠানো বাতিল করা হয়েছে।")
        user_data.pop(chat_id, None)

# বট চালু রাখা
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
