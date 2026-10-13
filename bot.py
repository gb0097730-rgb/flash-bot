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
        elapsed_before = user_data.get('elapsed', 0)
        current_time = int(time.time() * 1000)
        
        current_session_elapsed = (current_time - start_time) if start_time > 0 else 0
        total_elapsed = elapsed_before + current_session_elapsed
        remaining_ms = duration - total_elapsed
        
        if remaining_ms <= 0:
            return "⏰ အချိန်ကုန်ဆုံးသွားပါပြီ"
        
        remaining_mins = int(remaining_ms / (1000 * 60))
        remaining_secs = int((remaining_ms % (1000 * 60)) / 1000)
        
        if remaining_mins > 0:
            return f"⏳ {remaining_mins} မိနစ် {remaining_secs} စက္ကန့်"
        else:
            return f"⏳ {remaining_secs} စက္ကန့်"
            
    return "ဖွင့်ထားသည်"

# User တစ်ယောက်ချင်းစီအတွက် ထိန်းချုပ်ရန် Panel ပြသသည့် function
def show_user_panel(chat_id, message_id, check_id):
    try:
        response = requests.get(f"{FIREBASE_URL}/users/{check_id}.json")
        user_data = response.json()
    except:
        user_data = None

    if not user_data:
        bot.send_message(chat_id, f"❌ '{check_id}' ကို ရှာမတွေ့တော့ပါ။")
        return

    tg_name = user_data.get('tgName', 'အမည်မသိ')
    status = user_data.get('status', False)
    time_str = get_remaining_time_text(user_data)
    
    text = f"🔍 Check ID: `{check_id}`\n" \
           f"👤 Telegram Name: {tg_name}\n" \
           f"လက်ရှိ အခြေအနေ: {'ဖွင့်ထားသည်' if status else 'ပိတ်ထားသည်'}\n" \
           f"ကျန်ရှိသောအချိန် : {time_str}\n\n" \
           f"လိုချင်သော အချိန်ကို ရွေးချယ်ပါ -"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("♾️ အမြဲတမ်း (Always)", callback_data=f"always_{check_id}"))
    markup.row(
        InlineKeyboardButton("1 မိနစ်", callback_data=f"timed1_{check_id}"),
        InlineKeyboardButton("5 မိနစ်", callback_data=f"timed5_{check_id}"),
        InlineKeyboardButton("10 မိနစ်", callback_data=f"timed10_{check_id}")
    )
    markup.row(
        InlineKeyboardButton("20 မိနစ်", callback_data=f"timed20_{check_id}"),
        InlineKeyboardButton("30 မိနစ်", callback_data=f"timed30_{check_id}")
    )
    markup.row(
        InlineKeyboardButton("➕ 5m ပေါင်း", callback_data=f"add5_{check_id}"),
        InlineKeyboardButton("➕ 10m ပေါင်း", callback_data=f"add10_{check_id}")
    )
    markup.add(InlineKeyboardButton("❌ အကောင့်ပိတ်မည် (Block)", callback_data=f"block_{check_id}"))
    markup.add(InlineKeyboardButton("🔙 လူစာရင်းသို့ ပြန်သွားရန်", callback_data="back_to_list"))

    if message_id:
        try:
            bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="Markdown")
            return
        except:
            pass
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# /start Command (သို့မဟုတ် မီနူးခေါ်ရန်)
@bot.message_handler(commands=['start', 'users', 'list'])
def send_welcome(message):
    chat_id = message.chat.id
    
    try:
        response = requests.get(f"{FIREBASE_URL}/users.json")
        users_dict = response.json()
    except Exception as e:
        bot.reply_to(message, f"⚠️ Firebase ချိတ်ဆက်မှု အမှား: {e}")
        return

    if not users_dict:
        bot.reply_to(message, "⚡ FLASH BETBOT Admin Bot ⚡\n\n📭 လက်ရှိ စာရင်းသွင်းထားသော လူစာရင်း မရှိသေးပါ။ Check ID ကို တိုက်ရိုက် ပို့ပေးနိုင်ပါသည်။")
        return

    markup = InlineKeyboardMarkup()
    for check_id, data in users_dict.items():
        if isinstance(data, dict):
            tg_name = data.get('tgName', check_id)
            status = data.get('status', False)
            icon = "🟢" if status else "🔴"
            # နှိပ်လိုက်ရင် အဲ့ဒီ user ရဲ့ panel ထဲ ဝင်သွားမယ်
            markup.add(InlineKeyboardButton(f"{icon} {tg_name} ({check_id})", callback_data=f"selectuser_{check_id}"))

    markup.add(InlineKeyboardButton("🔄 စာရင်းကိုင် Refresh လုပ်ရန်", callback_data="refresh_list"))

    bot.reply_to(
        message,
        "⚡ FLASH BETBOT Admin Bot ⚡\n\n📋 **ခွင့်ပြုချက်ပေးထားသော / စာရင်းသွင်းထားသော လူစာရင်းများ:**\nအောက်ပါစာရင်းမှ လူတစ်ဦးချင်းစီကို နှိပ်၍ အချိန်သတ်မှတ်နိုင်ပါသည် -",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# Check ID ကို စာသားဖြင့် ပို့လာသောအခါ
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    check_id = message.text.strip().upper()
    show_user_panel(message.chat.id, None, check_id)

# ခလုတ်များကို နှိပ်လိုက်သောအခါ လုပ်ဆောင်ချက်
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if data == "back_to_list" or data == "refresh_list":
        # လူစာရင်း ပင်မစာမျက်နှာကို ပြန်ပြရန်
        try:
            response = requests.get(f"{FIREBASE_URL}/users.json")
            users_dict = response.json()
        except:
            users_dict = None

        if not users_dict:
            bot.edit_message_text("📭 လက်ရှိ စာရင်းသွင်းထားသော လူစာရင်း မရှိသေးပါ။", chat_id=chat_id, message_id=message_id)
            return

        markup = InlineKeyboardMarkup()
        for check_id, data_val in users_dict.items():
            if isinstance(data_val, dict):
                tg_name = data_val.get('tgName', check_id)
                status = data_val.get('status', False)
                icon = "🟢" if status else "🔴"
                markup.add(InlineKeyboardButton(f"{icon} {tg_name} ({check_id})", callback_data=f"selectuser_{check_id}"))

        markup.add(InlineKeyboardButton("🔄 စာရင်းကိုင် Refresh လုပ်ရန်", callback_data="refresh_list"))

        bot.edit_message_text(
            "📋 **ခွင့်ပြုချက်ပေးထားသော / စာရင်းသွင်းထားသော လူစာရင်းများ:**\nအောက်ပါစာရင်းမှ လူတစ်ဦးချင်းစီကို နှိပ်၍ အချိန်သတ်မှတ်နိုင်ပါသည် -",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    if data.startswith("selectuser_"):
        check_id = data.replace("selectuser_", "")
        show_user_panel(chat_id, message_id, check_id)
        return

    data_parts = data.split('_')
    if len(data_parts) < 2:
        return
        
    action = data_parts[0]
    check_id = data_parts[1]

    try:
        response = requests.get(f"{FIREBASE_URL}/users/{check_id}.json")
        user_data = response.json()
    except:
        user_data = None
    
    current_time = int(time.time() * 1000)

    if action == "always":
        requests.patch(f"{FIREBASE_URL}/users/{check_id}.json", json={
            'status': True,
            'mode': 'always',
            'startTime': 0,
            'duration': 0,
            'elapsed': 0
        })
        show_user_panel(chat_id, message_id, check_id)

    elif action.startswith("timed"):
        mins = int(action.replace("timed", ""))
        duration_ms = mins * 60 * 1000
        
        requests.patch(f"{FIREBASE_URL}/users/{check_id}.json", json={
            'status': True,
            'mode': 'timed',
            'startTime': current_time,
            'duration': duration_ms,
            'elapsed': 0
        })
        show_user_panel(chat_id, message_id, check_id)

    elif action.startswith("add"):
        add_mins = int(action.replace("add", ""))
        add_ms = add_mins * 60 * 1000
        
        old_status = user_data.get('status', False) if user_data else False
        old_mode = user_data.get('mode', '') if user_data else ''
        
        if old_status and old_mode == 'timed':
            old_start = user_data.get('startTime', current_time)
            old_duration = user_data.get('duration', 0)
            old_elapsed = user_data.get('elapsed', 0)
            
            current_session_elapsed = current_time - old_start
            total_elapsed = old_elapsed + current_session_elapsed
            remaining = old_duration - total_elapsed
            if remaining < 0:
                remaining = 0
                
            new_duration = remaining + add_ms
        else:
            new_duration = add_ms
            
        requests.patch(f"{FIREBASE_URL}/users/{check_id}.json", json={
            'status': True,
            'mode': 'timed',
            'startTime': current_time,
            'duration': new_duration,
            'elapsed': 0
        })
        show_user_panel(chat_id, message_id, check_id)

    elif action == "block":
        requests.patch(f"{FIREBASE_URL}/users/{check_id}.json", json={
            'status': False,
            'mode': 'blocked',
            'startTime': 0,
            'duration': 0,
            'elapsed': 0
        })
        show_user_panel(chat_id, message_id, check_id)

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        print(f"Webhook set to: {RENDER_URL}/{TOKEN}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
