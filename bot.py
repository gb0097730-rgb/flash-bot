import os
import threading
from flask import Flask
import firebase_admin
from firebase_admin import credentials, db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Render အတွက် Port error မတက်အောင် Web Server အသေးစား တစ်ခု ဖန်တီးခြင်း
web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Flash Bot is running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# Firebase Initialize
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": (
            "https://flash-1d21e-default-rtdb.europe-west1.firebasedatabase.app"
        )
    },
)

BOT_TOKEN = "8909968169:AAHkOH3mrnJ-GQSIV0rzBnb9bpdS5AtaGpI"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ FLASH BETBOT Admin Bot မှ ကြိုဆိုပါတယ် ⚡\n\nCheck ID ကို ပို့ပေးပါ၊ ဖွင့်ရန်/ပိတ်ရန် စီမံနိုင်ပါသည်။"
    )


async def handle_check_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.upper().startswith("FLASH"):
        check_id = text.upper()
        ref = db.reference(f"users/{check_id}")
        user_data = ref.get()

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ အကောင့်ဖွင့်မည် (Approve)",
                    callback_data=f"approve_{check_id}",
                ),
                InlineKeyboardButton(
                    "❌ အကောင့်ပိတ်မည် (Block)", callback_data=f"block_{check_id}"
                ),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        is_active = False
        if user_data and isinstance(user_data, dict):
            is_active = user_data.get("status", False)

        status_text = (
            "လက်ရှိ အခြေအနေ: ဖွင့်ထားသည်"
            if is_active
            else "လက်ရှိ အခြေအနေ: ပိတ်ထားသည်/မရှိသေးပါ"
        )

        await update.message.reply_text(
            f"🔍 Check ID: <code>{check_id}</code>\n{status_text}\n\nဒီအကောင့်ကို ဘာလုပ်မလဲ ရွေးချယ်ပါ -",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            "⚠️ မှန်ကန်သော Check ID ပုံစံ (ဥပမာ: FLASH-XXXXX) မဟုတ်ပါ။"
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    action, check_id = data.split("_", 1)
    ref = db.reference(f"users/{check_id}")

    if action == "approve":
        ref.update({"status": True})
        await query.edit_message_text(
            text=f"✅ Check ID: <code>{check_id}</code> ကို အောင်မြင်စွာ **ဖွင့်ပေးလိုက်ပါပြီ**။",
            parse_mode="HTML",
        )
    elif action == "block":
        ref.update({"status": False})
        await query.edit_message_text(
            text=f"❌ Check ID: <code>{check_id}</code> ကို အောင်မြင်စွာ **ပိတ်လိုက်ပါပြီ**။",
            parse_mode="HTML",
        )


def main():
    # Flask server ကို background မှာ သပ်သပ် run မယ်
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

    # Telegram Bot ကို run မယ်
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_check_id)
    )
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
