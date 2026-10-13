import os
import time
import requests
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot Token
TOKEN = "8746808077:AAHw3PnbPiy_f4gSdDMMrZg-mi2CvH0205o"
bot = telebot.TeleBot(TOKEN, threaded=False)

# Flask App
app = Flask(__name__)

# Firebase Realtime Database URL
FIREBASE_URL = "https://flash-1d21e-default-rtdb.europe-west1.firebasedatabase.app"

# Telegram Webhook Endpoint
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    else:
        return "Internal Server Error", 403

@app.route('/')
def home():
    return "Flash Bot Webhook is Active!"

# ကျန်ရှိသောအချိန်ကို တွက်ချက်သည့် ဖန်ရှင်
def get_remaining_time_text(user_data):
    if not user_data:
        return "အချက်အလက် မရှိပါ"
    
    status = user_data.get('status', False)
    if not status:
        return "ပိတ်ထားသည်"
    
    mode = user_data.get('mode', '')
    if mode == 'always':
        return "♾️ အမြဲတမ်း (Always)"
    elif mode == 'blocked':
        return "❌ ပိတ်ထားသည်"
    elif mode == 'timed':
        start_time = user_data.get('startTime', 0)
        duration = user_data.get('duration', 0)
        current_time = int(time.time() * 1000)
        
        elapsed_ms = current_time - start_time
        remaining_ms = duration - elapsed_ms
        
        if remaining_ms <= 0:
            return "⏰ အချိန်ကုန်ဆုံးသွားပါပြီ"
        
        remaining_mins = int(remaining_ms / (1000 * 60))
        remaining_secs = int((remaining_ms % (1000 * 60)) / 1000)
        
        if remaining_mins > 0:
            return f"⏳ {remaining_mins} မိနစ် {remaining_secs} စက္ကန့်"
        else:
            return f"⏳ {remaining_secs} စက္ကန့်"
            
    return "ဖွင့်ထားသည်"

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
    
    try:
        response = requests.get(f"{FIREBASE_URL}/users/{check_id}.json")
        user_data = response.json()
    except Exception as e:
        bot.reply_to(message, f"⚠️ Firebase ချိတ်ဆက်မှု အမှား: {e}")
        return

    if not user_data:
        bot.reply_to(
            message, 
            f"❌ '{check_id}' ကို Firebase ထဲတွင် ရှာမတွေ့ပါ။"
        )
        return

    tg_name = user_data.get('tgName', 'အမည်မသိ')
    status = user_data.get('status', False)
    time_str = get_remaining_time_text(user_data)
    
    text = f"🔍 *Check ID:* `{check_id}`\n" \
           f"👤 *Telegram Name:* {tg_name}\n" \
           f"လက်ရှိ အခြေအနေ: {'ဖွင့်ထားသည်' if status else 'ပိတ်ထားသည်'}\n" \
           f"ကျန်ရှိသောအချိန် : {time_str}\n\n" \
           f"ဘယ်လို ပုံစံမျိုး လုပ်ဆောင်မလဲ ရွေးချယ်ပါ -"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("♾️ အမြဲတမ်း ဖွင့်မည် (Always)", callback_data=f"always_{check_id}"))
    markup.add(InlineKeyboardButton("⏱️ ၁ မိနစ် သတ်မှတ်မည် (Timed 1m)", callback_data=f"timed1_{check_id}"))
    markup.add(InlineKeyboardButton("⏱️ ၅ မိနစ် သတ်မှတ်မည် (Timed 5m)", callback_data=f"timed5_{check_id}"))
    markup.add(InlineKeyboardButton("⏱️ ၁၀ မိနစ် သတ်မှတ်မည် (Timed 10m)", callback_data=f"timed10_{check_id}"))
    markup.add(InlineKeyboardButton("⏱️ မိနစ် ၃၀ သတ်မှတ်မည် (Timed 30m)", callback_data=f"timed30_{check_id}"))
    # အချိန်ပေါင်းထည့်ရန် ခလုတ်များ
    markup.add(InlineKeyboardButton("➕ ၅ မိနစ် ပေါင်းမည် (+5m)", callback_data=f"add5_{check_id}"))
    markup.add(InlineKeyboardButton("➕ ၁၀ မိနစ် ပေါင်းမည် (+10m)", callback_data=f"add10_{check_id}"))
    markup.add(InlineKeyboardButton("❌ အကောင့်ပိတ်မည် (Block)", callback_data=f"block_{check_id}"))

    bot.reply_to(message, text, reply_markup=markup, parse_mode="Markdown")

# ခလုတ်များကို နှိပ်လိုက်သောအခါ လုပ်ဆောင်ချက်
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data_parts = call.data.split('_')
    action = data_parts[0]
    check_id = data_parts[1]

    try:
        response = requests.get(f"{FIREBASE_URL}/users/{check_id}.json")
        user_data = response.json()
    except:
        user_data = None
    
    tg_name = user_data.get('tgName', '') if user_data else ''
    current_time = int(time.time() * 1000)

    if action == "always":
        requests.patch(f"{FIREBASE_URL}/users/{check_id}.json", json={
            'status': True,
            'mode': 'always',
            'startTime': 0,
            'duration': 0
        })
        bot.edit_message_text(
            f"🔍 *Check ID:* `{check_id}`\n"
            f"👤 *Telegram Name:* {tg_name}\n"
            f"လက်ရှိ အခြေအနေ: ဖွင့်ထားသည်\n"
            f"ကျန်ရှိသောအချိန် : *♾️ အမြဲတမ်း (Always)*",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )

    elif action.startswith("timed"):
        mins = int(action.replace("timed", ""))
        duration_ms = mins * 60 * 1000
        
        requests.patch(f"{FIREBASE_URL}/users/{check_id}.json", json={
            'status': True,
            'mode': 'timed',
            'startTime': current_time,
            'duration': duration_ms
        })
        bot.edit_message_text(
            f"🔍 *Check ID:* `{check_id}`\n"
            f"👤 *Telegram Name:* {tg_name}\n"
            f"လက်ရှိ အခြေအနေ: ဖွင့်ထားသည်\n"
            f"ကျန်ရှိသောအချိန် : *{mins} မိနစ်*",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )

    elif action.startswith("add"):
        add_mins = int(action.replace("add", ""))
        add_ms = add_mins * 60 * 1000
        
        old_status = user_data.get('status', False) if user_data else False
        old_mode = user_data.get('mode', '') if user_data else ''
        
        if old_status and old_mode == 'timed':
            old_start = user_data.get('startTime', current_time)
            old_duration = user_data.get('duration', 0)
            
            # လက်ရှိကျန်နေသေးသောအချိန်ကို တွက်မည် (သို့မဟုတ် အသစ်ပြန်စမည်)
            elapsed = current_time - old_start
            remaining = old_duration - elapsed
            if remaining < 0:
                remaining = 0
                
            new_duration = remaining + add_ms
        else:
            new_duration = add_ms
            
        requests.patch(f"{FIREBASE_URL}/users/{check_id}.json", json={
            'status': True,
            'mode': 'timed',
            'startTime': current_time,
            'duration': new_duration
        })
        
        total_mins = int(new_duration / (1000 * 60))
        bot.edit_message_text(
            f"🔍 *Check ID:* `{check_id}`\n"
            f"👤 *Telegram Name:* {tg_name}\n"
            f"လက်ရှိ အခြေအနေ: ဖွင့်ထားသည်\n"
            f"ကျန်ရှိသောအချိန် : *{total_mins} မိနစ် (+{add_mins} မိနစ် ပေါင်းပြီး)*",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )

    elif action == "block":
        requests.patch(f"{FIREBASE_URL}/users/{check_id}.json", json={
            'status': False,
            'mode': 'blocked',
            'startTime': 0,
            'duration': 0
        })
        bot.edit_message_text(
            f"🔍 *Check ID:* `{check_id}`\n"
            f"👤 *Telegram Name:* {tg_name}\n"
            f"လက်ရှိ အခြေအနေ: ပိတ်ထားသည်\n"
            f"❌ အကောင့်ပိတ်ပြီးပါပြီ။",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        print(f"Webhook set to: {RENDER_URL}/{TOKEN}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
