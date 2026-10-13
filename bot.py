import time
from firebase_admin import db

# Admin က /check <CheckID> (သို့မဟုတ် ခလုတ်နှိပ်စစ်ဆေးချိန်) လုပ်တဲ့အခါ
def check_user_status(message, check_id):
    # Firebase မှ User အချက်အလက်များကို ယူမည်
    ref = db.reference(f'users/{check_id}')
    user_data = ref.get()
    
    if not user_data:
        message.reply_text(f"❌ '{check_id}' ဖြင့် မှတ်ပုံတင်ထားသော အချက်အလက် မတွေ့ရှိပါ။")
        return

    # အချက်အလက်များ ထုတ်ယူခြင်း
    tg_name = user_data.get('tgName', 'အမည်မသိ')
    status = user_data.get('status', False)
    mode = user_data.get('mode', 'none')
    
    response_text = f"👤 **Telegram Name:** {tg_name}\n" \
                    f"🆔 **Check ID:** `{check_id}`\n" \
                    f"🟢 **Status:** {'Active (ဖွင့်ထားသည်)' if status else 'Inactive (ပိတ်ထားသည်)'}\n" \
                    f"⚙️ **Mode:** {mode.upper()}\n"

    # အကယ်၍ Timed Mode ဖြစ်ပြီး အလုပ်လုပ်နေပါက ကျန်ရှိသောအချိန်ကို တွက်ချက်မည်
    if status and mode == 'timed':
        start_time = user_data.get('startTime', 0)
        duration = user_data.get('duration', 0)
        current_time = int(time.time() * 1000) # Milliseconds
        
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
        response_text += f"⚠️ **အခြေအနေ:** ခွင့်ပြုချက် မရှိသေးပါ (သို့မဟုတ် သက်တမ်းကုန်ဆုံး)"

    message.reply_text(response_text, parse_mode="Markdown")
