import os
import time
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, ContextTypes, filters
from firebase_admin import credentials, initialize_app, db

# Flask App (Render ဆာဗာ အိပ်မသွားစေရန်)
app = Flask(__name__)

@app.route('/')
def home():
    return "Flash Bot is Live and Active!"

# Firebase ချိတ်ဆက်ခြင်း (သင့်ရဲ့ Database URL ကို ထည့်ပါ)
# အကယ်၍ json ဖိုင်သုံးထားပါက credentials.Certificate('path_to_key.json') ကို သုံးပါ
initialize_app({
    'databaseURL': 'https://flash-1d21e-default-rtdb.europe-west1.firebasedatabase.app'
})

# /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ **FLASH BETBOT Admin Bot** ⚡\n\nCheck ID (ဥပမာ - FLASH-795HY) ကို ပို့ပေးပါ။",
        parse_mode="Markdown"
    )

# Check ID ကို စာသားဖြင့် ပို့လာသောအခါ
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    check_id = update.message.text.strip().upper()
    context.user_data['active_check_id'] = check_id

    ref = db.reference(f'users/{check_id}')
    user_data = ref.get()

    if not user_data:
        await update.message.reply_text(f"❌ '{check_id}' ဖြင့် မှတ်ပုံတင်ထားသော အချက်အလက် မရှိပါ။")
        return

    tg_name = user_data.get('tgName', 'အမည်မသိ')
    status = user_data.get('status', False)
    mode = user_data.get('mode', 'none')

    text = f"🔍 **Check ID:** `{check_id}`\n" \
           f"👤 **Telegram Name:** {tg_name}\n" \
           f"လက်ရှိ အခြေအနေ: {'ဖွင့်ထားသည်' if status else 'ပိတ်ထားသည်'}\n\n" \
           f"ဘယ်လို ပုံစံမျိုး ဖွင့်ပေးမလဲ ရွေးချယ်ပါ -"

    keyboard = [
        [InlineKeyboardButton("♾️ အမြဲတမ်း ဖွင့်မည် (Always)", callback_data="mode_always")],
        [InlineKeyboardButton("⏱️ ၁ မိနစ် ဖွင့်မည် (Timed 1m)", callback_data="mode_timed_1m")],
        [InlineKeyboardButton("⏱️ ၁၀ မိနစ် ဖွင့်မည် (Timed 10m)", callback_data="mode_timed_10m")],
        [InlineKeyboardButton("❌ အကောင့်ပိတ်မည် (Block)", callback_data="mode_block")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ခလုတ်များကို နှိပ်လိုက်သောအခါ လုပ်ဆောင်ချက်
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    check_id = context.user_data.get('active_check_id')
    if not check_id:
        await query.edit_message_text("⚠️ သတိပေးချက် - ကျေးဇူးပြု၍ Check ID ကို အရင်ပြန်ပို့ပါ။")
        return

    ref = db.reference(f'users/{check_id}')
    data = ref.get()
    tg_name = data.get('tgName', '') if data else ''

    action = query.data

    if action == "mode_always":
        ref.update({
            'status': True,
            'mode': 'always',
            'startTime': 0,
            'duration': 0
        })
        await query.edit_message_text(f"✅ Check ID: {check_id} ({tg_name}) ကို **အမြဲတမ်း (Always)** အောင်မြင်စွာ ဖွင့်ပေးလိုက်ပါပြီ။", parse_mode="Markdown")

    elif action == "mode_timed_1m":
        duration_ms = 1 * 60 * 1000  # ၁ မိနစ်
        current_time = int(time.time() * 1000)
        ref.update({
            'status': True,
            'mode': 'timed',
            'startTime': current_time,
            'duration': duration_ms
        })
        await query.edit_message_text(f"✅ Check ID: {check_id} ({tg_name}) ကို **၁ မိနစ်** စာ အောင်မြင်စွာ ဖွင့်ပေးလိုက်ပါပြီ။", parse_mode="Markdown")

    elif action == "mode_timed_10m":
        duration_ms = 10 * 60 * 1000  # ၁၀ မိနစ်
        current_time = int(time.time() * 1000)
        ref.update({
            'status': True,
            'mode': 'timed',
            'startTime': current_time,
            'duration': duration_ms
        })
        await query.edit_message_text(f"✅ Check ID: {check_id} ({tg_name}) ကို **၁၀ မိနစ်** စာ အောင်မြင်စွာ ဖွင့်ပေးလိုက်ပါပြီ။", parse_mode="Markdown")

    elif action == "mode_block":
        ref.update({
            'status': False,
            'mode': 'blocked',
            'startTime': 0,
            'duration': 0
        })
        await query.edit_message_text(f"❌ Check ID: {check_id} ({tg_name}) ၏ ခွင့်ပြုချက်ကို ပိတ်လိုက်ပါပြီ။", parse_mode="Markdown")

# Telegram Bot ကို Background တွင် Run ခြင်း
def run_telegram_bot():
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # သင့်ရဲ့ Telegram Bot Token ထည့်ရန်
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.run_polling()

if __name__ == "__main__":
    import threading
    # Telegram Bot ကို Thread တစ်ခုအနေဖြင့် စတင်မည်
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Flask Web Server ကို Render Port ဖြင့် စတင်မည်
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
