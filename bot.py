import os
import time
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import firebase_admin
from firebase_admin import credentials, initialize_app, db

TOKEN = "8909968169:AAHkOH3mrnJ-GQSIV0rzBnb9bpdS5AtaGpI"
bot = telebot.TeleBot(TOKEN)

# Flask App (Render ဆာဗာ အိပ်မသွားစေရန်)
app = Flask(__name__)

@app.route('/')
def home():
    return "Flash Bot is Live and Active!"

# Firebase Database ကို Credentials မလိုဘဲ URL သီးသန့်ဖြင့် လုံခြုံစွာ ချိတ်ဆက်ခြင်း
if not firebase_admin._apps:
    try:
        initialize_app(options={
            'databaseURL': 'https://flash-1d21e-default-rtdb.europe-west1.firebasedatabase.app'
        })
    except Exception as e:
        print("Firebase Initialization Error:", e)

# /start Command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "⚡ *FLASH BETBOT Admin Bot* ⚡\n\nCheck ID (ဥပမာ - FLASH-795HY) ကို ပို့ပေးပါ။",
        parse_mode="Markdown"
    )

# Check ID ကို စာသားဖြင့် ပို့လာသောအခါ
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    check_id = message.text.strip().upper()
    
    ref = db.reference(f'users/{check_id}')
    user_data = ref.get()

    if not user_data:
        bot.reply_to(message, f"❌ '{check_id}' ဖြင့် Firebase ထဲတွင် မှတ်ပုံတင်ထားသော အချက်အလက် မရှိပါ။ ကျေးဇူးပြု၍ ဝဘ်ဆိုက်တွင် Check ID အရင်ထုတ်ပါ။")
        return

    tg_name = user_data.get('tgName', 'အမည်မသိ')
    status = user_data.get('status', False)
    
    text = f"🔍 *Check ID:* `{check_id}`\n" \
           f"👤 *Telegram Name:* {tg_name}\n" \
           f"လက်ရှိ အခြေအနေ: {'ဖွင့်ထားသည်' if status else 'ပိတ်ထားသည်'}\n\n" \
           f"ဘယ်လို ပုံစံမျိုး ဖွင့်ပေးမလဲ ရွေးချယ်ပါ -"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("♾️ အမြဲတမ်း ဖွင့်မည် (Always)", callback_data=f"always_{check_id}"))
    markup.add(InlineKeyboardButton("⏱️ ၁ မိနစ် ဖွင့်မည် (Timed 1m)", callback_data=f"timed1_{check_id}"))
    markup.add(InlineKeyboardButton("⏱️ ၁၀ မိနစ် ဖွင့်မည် (Timed 10m)", callback_data=f"timed10_{check_id}"))
    markup.add(InlineKeyboardButton("❌ အကောင့်ပိတ်မည် (Block)", callback_data=f"block_{check_id}"))

    bot.reply_to(message, text, reply_markup=markup, parse_mode="Markdown")

# ခလုတ်များကို နှိပ်လိုက်သောအခါ လုပ်ဆောင်ချက်
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data_parts = call.data.split('_')
    action = data_parts[0]
    check_id = data_parts[1]

    ref = db.reference(f'users/{check_id}')
    user_data = ref.get()
    tg_name = user_data.get('tgName', '') if user_data else ''

    if action == "always":
        ref.update({
            'status': True,
            'mode': 'always',
            'startTime': 0,
            'duration': 0
        })
        bot.edit_message_text(
            f"✅ Check ID: `{check_id}` ({tg_name}) ကို *အမြဲတမ်း (Always)* အောင်မြင်စွာ ဖွင့်ပေးလိုက်ပါပြီ။",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )

    elif action == "timed1":
        duration_ms = 1 * 60 * 1000  # ၁ မိနစ်
        current_time = int(time.time() * 1000)
        ref.update({
            'status': True,
            'mode': 'timed',
            'startTime': current_time,
            'duration': duration_ms
        })
        bot.edit_message_text(
            f"✅ Check ID: `{check_id}` ({tg_name}) ကို *၁ မိနစ်* စာ အောင်မြင်စွာ ဖွင့်ပေးလိုက်ပါပြီ။",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )

    elif action == "timed10":
        duration_ms = 10 * 60 * 1000  # ၁၀ မိနစ်
        current_time = int(time.time() * 1000)
        ref.update({
            'status': True,
            'mode': 'timed',
            'startTime': current_time,
            'duration': duration_ms
        })
        bot.edit_message_text(
            f"✅ Check ID: `{check_id}` ({tg_name}) ကို *၁၀ မိနစ်* စာ အောင်မြင်စွာ ဖွင့်ပေးလိုက်ပါပြီ။",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )

    elif action == "block":
        ref.update({
            'status': False,
            'mode': 'blocked',
            'startTime': 0,
            'duration': 0
        })
        bot.edit_message_text(
            f"❌ Check ID: `{check_id}` ({tg_name}) ၏ ခွင့်ပြုချက်ကို ပိတ်လိုက်ပါပြီ။",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )

# Telegram Bot ကို Background တွင် Run ခြင်း
def run_telegram_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    import threading
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Flask Web Server ကို Render Port ဖြင့် စတင်မည်
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
