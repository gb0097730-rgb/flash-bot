import os
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import firebase_admin
from firebase_admin import credentials, db

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

try:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://flash-1d21e-default-rtdb.europe-west1.firebasedatabase.app'
    })
    print("Firebase ချိတ်ဆက်မှု အောင်မြင်ပါသည်။")
except Exception as e:
    print(f"Firebase ချိတ်ဆက်ရာတွင် အမှားရှိပါသည်: {e}")

TOKEN = "8909968169:AAHkOH3mrnJ-GQSIV0rzBnb9bpdS5AtaGpI"

app_flask = Flask(__name__)
application = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ARIES BETBOT Admin Bot သို့ ကြိုဆိုပါသည်။ Check ID များကို ဤနေရာတွင် စစ်ဆေးပေးမည် ဖြစ်ပါသည်။")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("ARIES-"):
        check_id = text
        keyboard = [
            [InlineKeyboardButton("✅ APPROVE (ခွင့်ပြုမည်)", callback_data=f"approve_{check_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"📥 **Check ID အသစ် ရောက်ရှိလာပါပြီ**\n\nID: `{check_id}`\n\nခွင့်ပြုရန် အောက်ပါခလုတ်ကို နှိပ်ပါ။",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("ကျေးဇူးပြု၍ မှန်ကန်သော ARIES Check ID ကို ပို့ပေးပါ။")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("approve_"):
        check_id = data.split("_")[1]
        try:
            ref = db.reference(f'users/{check_id}')
            ref.update({'status': True})
            await query.edit_message_text(
                text=f"✅ Check ID: `{check_id}` ကို အောင်မြင်စွာ ခွင့်ပြု (Approve) ပေးလိုက်ပါပြီ။",
                parse_mode="Markdown"
            )
        except Exception as e:
            await query.edit_message_text(text=f"❌ အမှားအယွင်း ရှိနေပါသည်: {str(e)}")

@app_flask.route('/')
def index():
    return "ARIES BETBOT Admin Bot is running!"

if __name__ == '__main__':
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling()
