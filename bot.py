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

# Firebase Initialize
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(
    cred, {"databaseURL": "https://flash-1d21e-default-rtdb.firebaseio.com/"}
)

BOT_TOKEN = "8909968169:AAHkOH3mrnJ-GQSIV0rzBnb9bpdS5AtaGpI"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ ARIES BETBOT Admin Bot မှ ကြိုဆိုပါတယ် ⚡\n\nCheck ID (ဥပမာ - ARIES-12345) ကို ပို့ပေးပါ၊ ဖွင့်ရန်/ပိတ်ရန် စီမံနိုင်ပါတယ်။"
    )


# Check ID ရောက်လာတဲ့အခါ ဖွင့်ရန်/ပိတ်ရန် ခလုတ်ပြပေးမယ့် ပုံစံ
async def handle_check_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("ARIES-"):
        check_id = text
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

        status_text = (
            "လက်ရှိ အခြေအနေ: ဖွင့်ထားသည်"
            if user_data and user_data.get("status")
            else "လက်ရှိ အခြေအနေ: ပိတ်ထားသည်/မရှိသေးပါ"
        )

        await update.message.reply_text(
            f"🔍 Check ID: <code>{check_id}</code>\n{status_text}\n\nဒီအကောင့်ကို ဘာလုပ်မလဲ ရွေးချယ်ပါ -",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            "⚠️ မှန်ကန်သော Check ID ပုံစံ (ဥပမာ: ARIES-XXXXX) မဟုတ်ပါ။"
        )


# ခလုတ်နှိပ်လိုက်တဲ့အခါ Firebase မှာ True/False ပြောင်းပေးမယ့် the logic
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
