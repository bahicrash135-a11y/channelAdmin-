import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

# আপনার বটের টোকেন এখানে দিন
TOKEN = "8338804278:AAGAIJE02dT8zW7vX35ynlqPpcmoxjBe_bs"
bot = telebot.TeleBot(TOKEN)

# অ্যাডমিন ইউজারনেম (এখানে আপনার ইউজারনেম দেওয়া আছে)
ADMIN_USERNAME = "SUNNY_BRO1"

# চ্যানেল সেভ রাখার জন্য ডাটাবেস ফাইল
DATA_FILE = "bot_data.json"
user_data = {}

# অ্যাডমিন কি না তা চেক করার ফাংশন
def is_admin(message_or_call):
    username = message_or_call.from_user.username
    if username and username.upper() == ADMIN_USERNAME.upper():
        return True
    return False

# একাধিক চ্যানেল সেভ করার ফাংশনগুলো
def load_channels():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                return data.get("channels", [])
            except:
                return []
    return []

def add_channel(channel_id):
    channels = load_channels()
    if channel_id not in channels:
        channels.append(channel_id)
        with open(DATA_FILE, 'w') as f:
            json.dump({"channels": channels}, f, indent=4)
        return True
    return False

def remove_channel(channel_id):
    channels = load_channels()
    if channel_id in channels:
        channels.remove(channel_id)
        with open(DATA_FILE, 'w') as f:
            json.dump({"channels": channels}, f, indent=4)
        return True
    return False

# স্টার্ট কমান্ড
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ আপনি এই বটের অ্যাডমিন নন। শুধুমাত্র @SUNNY_BRO1 এটি ব্যবহার করতে পারবেন।")
        return
        
    text = (
        "🤖 **অ্যাডমিন প্যানেলে স্বাগতম @SUNNY_BRO1!**\n\n"
        "১. নতুন চ্যানেল অ্যাড করতে টাইপ করুন:\n👉 `/setchannel চ্যানেলের_আইডি`\n\n"
        "২. কোনো চ্যানেল ডিলিট করতে টাইপ করুন:\n👉 `/delchannel চ্যানেলের_আইডি`\n\n"
        "৩. পোস্ট করতে টাইপ করুন:\n👉 `/newpost`\n\n"
        "*(আপনি যতখুশি চ্যানেল অ্যাড করতে পারবেন)*"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

# চ্যানেল সেট করার কমান্ড
@bot.message_handler(commands=['setchannel'])
def handle_setchannel(message):
    if not is_admin(message):
        return
        
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "⚠️ **সঠিক নিয়ম:**\n`/setchannel @yourchannel` অথবা প্রাইভেট হলে `/setchannel -10012345678`", parse_mode='Markdown')
        return
        
    channel_id = args[1].strip()
    if add_channel(channel_id):
        bot.reply_to(message, f"✅ **চ্যানেল সফলভাবে অ্যাড করা হয়েছে!**\nযুক্ত করা চ্যানেল: `{channel_id}`", parse_mode='Markdown')
    else:
        bot.reply_to(message, f"⚠️ এই চ্যানেলটি (`{channel_id}`) আগেই লিস্টে অ্যাড করা আছে।", parse_mode='Markdown')

# চ্যানেল ডিলিট করার কমান্ড
@bot.message_handler(commands=['delchannel'])
def handle_delchannel(message):
    if not is_admin(message):
        return
        
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "⚠️ **সঠিক নিয়ম:**\n`/delchannel @yourchannel`", parse_mode='Markdown')
        return
        
    channel_id = args[1].strip()
    if remove_channel(channel_id):
        bot.reply_to(message, f"🗑️ **চ্যানেল সফলভাবে রিমুভ করা হয়েছে!**\nরিমুভ করা চ্যানেল: `{channel_id}`", parse_mode='Markdown')
    else:
        bot.reply_to(message, "⚠️ এই চ্যানেলটি আপনার লিস্টে পাওয়া যায়নি।")

# নতুন পোস্ট করার কমান্ড (এখান থেকে চ্যানেল সিলেক্ট করতে হবে)
@bot.message_handler(commands=['newpost'])
def handle_newpost(message):
    if not is_admin(message):
        return
        
    channels = load_channels()
    if not channels:
        bot.reply_to(message, "⚠️ আপনার লিস্টে কোনো চ্যানেল নেই। দয়া করে আগে `/setchannel` কমান্ড দিয়ে চ্যানেল অ্যাড করুন।")
        return
        
    markup = InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        markup.add(InlineKeyboardButton(text=f"📢 {ch}", callback_data=f"select_{ch}"))
        
    bot.reply_to(message, "👇 **কোন চ্যানেলে পোস্ট করতে চান তা নিচের বাটন থেকে নির্বাচন করুন:**", reply_markup=markup)

# চ্যানেলের বাটনে ক্লিক করলে যা হবে
@bot.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def handle_channel_selection(call):
    if not is_admin(call):
        bot.answer_callback_query(call.id, "❌ আপনি এই বটের অ্যাডমিন নন।", show_alert=True)
        return
    
    # লোডিং অ্যানিমেশন বন্ধ করার জন্য
    bot.answer_callback_query(call.id)
        
    selected_channel = call.data.replace('select_', '')
    
    if call.message.chat.id not in user_data:
        user_data[call.message.chat.id] = {}
    user_data[call.message.chat.id]['selected_channel'] = selected_channel
    
    bot.edit_message_text(f"✅ আপনি **{selected_channel}** নির্বাচন করেছেন।", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown')
    
    msg = bot.send_message(call.message.chat.id, "📝 **এবার আপনার পোস্টের ম্যাটেরিয়াল দিন:**\n\nআপনি চাইলে কোনো **টেক্সট (Text)**, **ছবি (Photo)** অথবা **ভিডিও (Video)** পাঠাতে পারেন। (ছবি বা ভিডিওর সাথে চাইলে ক্যাপশনও লিখে দিতে পারেন।)")
    
    bot.register_next_step_handler(msg, process_media)

# মিডিয়া (টেক্সট/ছবি/ভিডিও) প্রসেস করা
def process_media(message):
    if not is_admin(message):
        return
        
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {}
        
    if message.content_type == 'text':
        user_data[message.chat.id]['type'] = 'text'
        user_data[message.chat.id]['content'] = message.html_text
        
    elif message.content_type == 'photo':
        user_data[message.chat.id]['type'] = 'photo'
        user_data[message.chat.id]['file_id'] = message.photo[-1].file_id 
        user_data[message.chat.id]['content'] = message.html_caption if message.html_caption else ""
        
    elif message.content_type == 'video':
        user_data[message.chat.id]['type'] = 'video'
        user_data[message.chat.id]['file_id'] = message.video.file_id
        user_data[message.chat.id]['content'] = message.html_caption if message.html_caption else ""
    else:
        msg = bot.reply_to(message, "⚠️ এই ফরম্যাটটি সাপোর্ট করে না। দয়া করে টেক্সট, ছবি বা ভিডিও দিন।")
        bot.register_next_step_handler(msg, process_media)
        return

    text = (
        "✅ **ফাইল রিসিভ হয়েছে!**\n\n"
        "এবার বাটনগুলো দিন (নিচের নিয়মে):\n"
        "`বাটনের নাম | লিংক | কালার` (green/red/blue)\n\n"
        "**উদাহরণ:** `REGISTER NOW | https://elix.com | green`\n\n"
        "*যদি কোনো বাটন না চান, তবে শুধু `skip` লিখুন।*"
    )
    msg = bot.reply_to(message, text, parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_buttons)

# বাটন প্রসেস করে চ্যানেলে পোস্ট করা
def process_buttons(message):
    if not is_admin(message):
        return
        
    markup = InlineKeyboardMarkup(row_width=1)
    
    if message.text and message.text.lower() != 'skip':
        try:
            lines = message.text.split('\n')
            for line in lines:
                parts = line.split('|')
                if len(parts) >= 2:
                    btn_text = parts[0].strip()
                    btn_url = parts[1].strip()
                    
                    # কালার অপশন (ইমোজির মাধ্যমে)
                    if len(parts) == 3:
                        color = parts[2].strip().lower()
                        if color in ['green', 'success']:
                            btn_text = f"🟢 {btn_text}"
                        elif color in ['red', 'danger']:
                            btn_text = f"🔴 {btn_text}"
                        elif color in ['blue', 'primary']:
                            btn_text = f"🔵 {btn_text}"
                    
                    markup.add(InlineKeyboardButton(text=btn_text, url=btn_url))
        except Exception as e:
            bot.reply_to(message, "⚠️ বাটনের ফরম্যাটে সমস্যা হয়েছে। বাটন ছাড়া পাঠানো হচ্ছে।")

    # সেশন ডেটা নিরাপদ উপায়ে রিড করা
    chat_data = user_data.get(message.chat.id, {})
    channel_id = chat_data.get('selected_channel')
    post_type = chat_data.get('type')
    post_content = chat_data.get('content')
    file_id = chat_data.get('file_id')
    
    if not channel_id or not post_type:
        bot.reply_to(message, "❌ সেশন শেষ হয়ে গেছে বা কোনো ভুল হয়েছে। অনুগ্রহ করে আবার `/newpost` দিন।", parse_mode='Markdown')
        return
        
    try:
        if post_type == 'text':
            bot.send_message(chat_id=channel_id, text=post_content, reply_markup=markup, parse_mode='HTML')
            
        elif post_type == 'photo':
            bot.send_photo(chat_id=channel_id, photo=file_id, caption=post_content, reply_markup=markup, parse_mode='HTML')
            
        elif post_type == 'video':
            bot.send_video(chat_id=channel_id, video=file_id, caption=post_content, reply_markup=markup, parse_mode='HTML')
            
        bot.reply_to(message, f"🎉 **সফল!** আপনার পোস্টটি সফলভাবে `{channel_id}` চ্যানেলে পাবলিশ করা হয়েছে।", parse_mode='Markdown')
        
        # সফল পোস্টের পর সাময়িক ডেটা ডিলিট করে দেওয়া
        if message.chat.id in user_data:
            del user_data[message.chat.id]
        
    except telebot.apihelper.ApiTelegramException as e:
        bot.reply_to(message, f"❌ **পোস্ট পাঠানো যায়নি!**\n\n*(Error: {e.description})*\n\nদয়া করে চেক করুন বটটি ওই চ্যানেলে অ্যাডমিন আছে কিনা এবং পোস্টের মেসেজ ফরম্যাটটি সঠিক আছে কিনা।", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ একটি অজানা ত্রুটি হয়েছে: {e}")

if __name__ == '__main__':
    print("Admin Controller Bot is running...")
    bot.infinity_polling()
