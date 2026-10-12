async def handle_check_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # FLASH နဲ့စတဲ့ စာသားမှန်သမျှကို လက်ခံရန်
    if text.upper().startswith("FLASH"):
        check_id = text.upper()
        ref = db.reference(f"users/{check_id}")
        user_data = ref.get()
        
        keyboard = [
            [
                InlineKeyboardButton("✅ အကောင့်ဖွင့်မည် (Approve)", callback_data=f"approve_{check_id}"),
                InlineKeyboardButton("❌ အကောင့်ပိတ်မည် (Block)", callback_data=f"block_{check_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        is_active = False
        if user_data and isinstance(user_data, dict):
            is_active = user_data.get("status", False)
            
        status_text = "လက်ရှိ အခြေအနေ: ဖွင့်ထားသည်" if is_active else "လက်ရှိ အခြေအနေ: ပိတ်ထားသည်/မရှိသေးပါ"
        
        await update.message.reply_text(
            f"🔍 Check ID: <code>{check_id}</code>\n{status_text}\n\nဒီအကောင့်ကို ဘာလုပ်မလဲ ရွေးချယ်ပါ -",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("⚠️ မှန်ကန်သော Check ID ပုံစံ (ဥပမာ: FLASH-XXXXX) မဟုတ်ပါ။")
