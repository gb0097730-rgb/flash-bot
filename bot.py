import os
import time
from flask import Flask
from firebase_admin import credentials, initialize_app, db

# Flask App တည်ဆောက်ခြင်း (Render Sleep မဖြစ်စေရန်အတွက်)
app = Flask(__name__)

@app.route('/')
def home():
    return "Flash Bot is Active!"

# Firebase ချိတ်ဆက်ခြင်း (သင့်ရဲ့ Firebase JSON ဖိုင်အမည်ကို ထည့်ပါ)
# cred = credentials.Certificate("firebase_key.json")
# initialize_app(cred, {
#     'databaseURL': 'https://flash-1d21e-default-rtdb.europe-west1.firebasedatabase.app'
# })

# Telegram Bot စတင် Run ခြင်းနှင့် Admin မှ Check ID စစ်ဆေးရန် Function
def check_user_status(message, check_id):
    ref = db.reference(f'users/{check_id}')
    user_data = ref.get()
    
    if not user_data:
        message.reply_text(f"❌ '{check_id}' ဖြင့် မှတ်ပုံတင်ထားသော အချက်အလက် မတွေ့ရှိပါ။")
        return

    tg_name = user_data.get('tgName', 'အမည်မသိ')
    status = user_data.get('status', False)
    mode = user_data.get('mode', 'none')
    
    response_text = f"👤 **Telegram Name:** {tg_name}\n" \
                    f"🆔 **Check ID:** `{check_id}`\n" \
                    f"🟢 **Status:** {'Active (ဖွင့်ထားသည်)' if status else 'Inactive (ပိတ်ထားသည်)'}\n" \
                    f"⚙️ **Mode:** {mode.upper()}\n"

    if status and mode == 'timed':
        start_time = user_data.get('startTime', 0)
        duration = user_data.get('duration', 0)
        current_time = int(time.time() * 1000)
        
        elapsed = current_time - start_time
        time_left = duration - elapsed
        
        if time_left > 0:
            total_seconds = int(time_left / 1000)
            mins = total_seconds // 60
            secs = total_seconds % 60
            response_text += f"⏱️ **ကျန်ရှိသောအချိန်:** {mins} မိနစ် {secs} စက္ကန့်"
        else:
            response_text += f"⏱️ **ကျန်ရှိသောအချိန်:** အချိန်ကုန်ဆုံးသွားပါပြီ (Expired)"
            
    elif status and mode == 'always':
        response_text += f"♾️ **အမျိုးအစား:** ၂၄ နာရီ အမြဲတမ်း ဖွင့်ထားသည် (Always Active)"
    else:
        response_text += f"⚠️ **အခြေအနေ:** ခွင့်ပြုချက် မရှိသေးပါ"

    message.reply_text(response_text, parse_mode="Markdown")

# Render မှပေးသော Port ဖြင့် Flask Server ကို စတင် Run ခြင်း
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
