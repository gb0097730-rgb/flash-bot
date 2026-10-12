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

# Render အတွက် Port error မတက်အောင် Web Server အသေးစား
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

# Admin တွေအတွက် အချိန် (မိနစ်) တောင်းနေတဲ့ state များကို မှတ်ထားရန်
waiting_minutes = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ FLASH BETBOT Admin Bot ⚡\n\nCheck ID (ဥပမာ - FLASH-12345) ကို ပို့ပေးပါ။"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # 1. Admin က မိနစ်အရေအတွက် (ဥပမာ: 10) ရိုက်ထည့်လိုက်တဲ့အခါ
    if user_id in waiting_minutes:
        check_id = waiting_minutes[user_id]
        try:
            minutes = int(text)
            duration_ms = minutes * 60 * 1000

            # Firebase သို့ အချိန်နှင့်တကွ ဖွင့်ပေးခြင်း
            ref = db.reference(f"users/{check_id}")
            ref.update(
                {
                    "status": True,
                    "mode": "timed",
                    "duration": duration_ms,
                    "startTime": db.SERVER_TIMESTAMP,
                }
            )

            # state ကို ရှင်းထုတ်မည်
            del waiting_minutes[user_id]

            await update.message.reply_text(
                f"✅ Check ID: <code>{check_id}</code> ကို **{minutes} မိနစ်** စာ အောင်မြင်စွာ ဖွင့်ပေးလိုက်ပါပြီ။",
                parse_mode="HTML",
            )
            return
        except ValueError:
            await update.message.reply_text(
                "⚠️ ကျေးဇူးပြု၍ ဂဏန်းဖြင့်သာ (ဥပမာ: 10 သို့မဟုတ် 20) တိတိကျကျ ရိုက်ထည့်ပါ။"
            )
            return

    # 2. Check ID (ဥပမာ - FLASH-XXXXX) ပို့လာသည့်အခါ
    if text.upper().startswith("FLASH"):
        check_id = text.upper()
        ref = db.reference(f"users/{check_id}")
        user_data = ref.get()

        keyboard = [
            [
                InlineKeyboardButton(
                    "♾️ အမြဲတမ်း ဖွင့်မည် (Always)",
                    callback_data=f"mode_always_{check_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⏳ အချိန်သတ်မှတ် ဖွင့်မည် (Timed)",
                    callback_data=f"mode_timed_{check_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ အကောင့်ပိတ်မည် (Block / Reset)",
                    callback_data=f"block_{check_id}",
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        is_active = False
        mode = "none"
        if user_data and isinstance(user_data, dict):
            is_active = user_data.get("status", False)
            mode = user_data.get("mode", "none")

        status_text = (
            f"လက်ရှိ အခြေအနေ: ဖွင့်ထားသည် ({mode})"
            if is_active
            else "လက်ရှိ အခြေအနေ: ပိတ်ထားသည်"
        )

        await update.message.reply_text(
            f"🔍 Check ID: <code>{check_id}</code>\n{status_text}\n\nဘယ်လို ပုံစံမျိုး ဖွင့်ပေးမလဲ ရွေးချယ်ပါ -",
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
    user_id = update.effective_user.id
    chat_id = query.message.chat_id

    if data.startswith("mode_always_"):
        check_id = data.replace("mode_always_", "")
        ref = db.reference(f"users/{check_id}")
        ref.update(
            {"status": True, "mode": "always", "startTime": None, "duration": None}
        )
        await query.edit_message_text(
            text=f"✅ Check ID: <code>{check_id}</code> ကို **အမြဲတမ်း (Time Limit မပါဘဲ)** ဖွင့်ပေးလိုက်ပါပြီ။",
            parse_mode="HTML",
        )

    elif data.startswith("mode_timed_"):
        check_id = data.replace("mode_timed_", "")
        # ဒီ Admin အတွက် ဘယ် Check ID ကို အချိန်ပေးရမလဲ မှတ်ထားမည်
        waiting_minutes[user_id] = check_id

        await query.edit_message_text(
            text=f"⏳ Check ID: <code>{check_id}</code> အတွက် **ဘယ်နှစ်မိနစ်** သုံးခွင့်ပေးမလဲ?\n\n(ဥပမာ: 10 သို့မဟုတ် 15 ဟု ဂဏန်းဖြင့် တိုက်ရိုက်ရိုက်ပြီး ပို့ပေးပါ)",
            parse_mode="HTML",
        )

    elif data.startswith("block_"):
        check_id = data.replace("block_", "")
        ref = db.reference(f"users/{check_id}")
        ref.update(
            {"status": False, "mode": "blocked", "startTime": 0, "duration": 0}
        )
        await query.edit_message_text(
            text=f"❌ Check ID: <code>{check_id}</code> ကို **ပိတ်လိုက်ပါပြီ** (အချိန် 0 သို့ ပြန်ရောက်သွားပါပြီ)။",
            parse_mode="HTML",
        )


def main():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
