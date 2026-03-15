import collections
if not hasattr(collections, 'MutableMapping'):
    import collections.abc
    collections.MutableMapping = collections.abc.MutableMapping
    collections.Mapping = collections.abc.Mapping
    collections.Callable = collections.abc.Callable

import telebot
from telebot import types
import os
from flask import Flask
from threading import Thread

# --- إعداد خادم الوهمي للبقاء حياً (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    # Render يستخدم المنفذ 8080 بشكل افتراضي أو يمكنك تركه يحدد تلقائياً
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- الإعدادات الأصلية لبوتك ---
API_TOKEN = '8536497984:AAFreSUHUUp12w_SNs2WH1RQO3KNcBhqmyk'
ADMIN_ID = 6671521979 
POST_CHANNEL_ID = '@BB_VBN' 
CHANNELS = ['@BB_VBN', '@VPN_Dzz'] 

bot = telebot.TeleBot(API_TOKEN)

def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True 
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['creator', 'administrator', 'member']:
                return False
        except:
            return False
    return True

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📢 نشر إعلان بيع', '🔍 نشر طلب شراء')
    markup.row('🔄 طلب تبادل')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    if is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "مرحباً بك في سوق الخدمات 💎", reply_markup=main_keyboard())
    else:
        markup = types.InlineKeyboardMarkup()
        for chan in CHANNELS:
            clean_chan = chan.replace('@', '')
            markup.add(types.InlineKeyboardButton(f"📢 إشترك في {chan}", url=f"https://t.me/{clean_chan}"))
        markup.add(types.InlineKeyboardButton("✅ تم الاشتراك", callback_data="check_sub"))
        bot.send_message(message.chat.id, "⚠️ اشترك أولاً ثم اضغط على الزر.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ تم التفعيل!", reply_markup=main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

@bot.message_handler(func=lambda message: message.text in ['📢 نشر إعلان بيع', '🔍 نشر طلب شراء', '🔄 طلب تبادل'])
def handle_publish(message):
    if not is_subscribed(message.from_user.id): return start(message)
    msg = bot.send_message(message.chat.id, f"📝 أرسل تفاصيل ({message.text}) الآن:")
    bot.register_next_step_handler(msg, process_ad, message.text)

def process_ad(message, ad_type):
    user_username = message.from_user.username
    user_id = message.from_user.id
    contact_info = f"t.me/{user_username}" if user_username else f"tg://user?id={user_id}"
    user_info = f"\n\n👤 الناشر: @{user_username or 'مخفي'}\n🆔 الأيدي: `{user_id}`"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ قبول ونشر", callback_data=f"acc_{user_id}_{user_username or 'no'}"),
               types.InlineKeyboardButton("❌ رفض", callback_data=f"rej_{user_id}"))

    if message.content_type == 'photo':
        caption = f"✨ **{ad_type}** ✨\n\n{message.caption}\n{user_info}"
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode='Markdown')
    else:
        text = f"✨ **{ad_type}** ✨\n\n{message.text}\n{user_info}"
        bot.send_message(ADMIN_ID, text, reply_markup=markup, parse_mode='Markdown')
    
    bot.send_message(message.chat.id, "✅ تم إرسال طلبك للإدارة.")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("acc_", "rej_")))
def handle_admin_action(call):
    data = call.data.split('_')
    action = data[0]
    u_id = data[1]
    
    if action == "acc":
        u_username = data[2]
        contact_url = f"https://t.me/{u_username}" if u_username != 'no' else f"tg://user?id={u_id}"
        chan_markup = types.InlineKeyboardMarkup()
        chan_markup.add(types.InlineKeyboardButton("📩 إضغط هنا للمراسلة", url=contact_url))
        
        warning = "\n\n⚠️ **الإدارة غير مسؤولة عن أي تعامل خارج البوت.**"
        content = call.message.caption if call.message.content_type == 'photo' else call.message.text
        final_text = content.split("🆔 الأيدي:")[0] + warning
        
        try:
            if call.message.content_type == 'photo':
                bot.send_photo(POST_CHANNEL_ID, call.message.photo[-1].file_id, caption=final_text, reply_markup=chan_markup, parse_mode='Markdown')
            else:
                bot.send_message(POST_CHANNEL_ID, final_text, reply_markup=chan_markup, parse_mode='Markdown')
            bot.send_message(int(u_id), "🎉 تم قبول ونشر إعلانك!")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ خطأ في النشر: {e}")
            
    bot.delete_message(call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    # تشغيل خادم الويب في الخلفية
    keep_alive()
    # تشغيل البوت
    print("Bot is running...")
    bot.infinity_polling()

