import collections
if not hasattr(collections, 'MutableMapping'):
    import collections.abc
    collections.MutableMapping = collections.abc.MutableMapping
    collections.Mapping = collections.abc.Mapping
    collections.Callable = collections.abc.Callable

import telebot
from telebot import types
import time

# --- الإعدادات المعدلة بالتوكن الجديد ---
API_TOKEN = '8536497984:AAEfSfujRDi3rteJhgE7jdVFJPDwoqd3hzk'
ADMIN_ID = 6671521979 

# قائمة القنوات المطلوب الاشتراك بها
CHANNELS = ['@BB_VBN', '@VPN_Dzz'] 
# القناة التي يتم النشر فيها عند القبول
POST_CHANNEL = '@BB_VBN' 

bot = telebot.TeleBot(API_TOKEN)
bot.remove_webhook()
time.sleep(1)

user_data = {}

def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True 
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['creator', 'administrator', 'member']:
                return False
        except Exception:
            return False
    return True

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📢 نشر إعلان بيع', '🔍 نشر طلب شراء')
    markup.row('🔄 طلب تبادل')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if is_subscribed(user_id):
        bot.send_message(message.chat.id, "مرحباً بك في سوق الخدمات 💎", reply_markup=main_keyboard())
    else:
        markup = types.InlineKeyboardMarkup()
        for chan in CHANNELS:
            clean_chan = chan.replace('@', '')
            markup.add(types.InlineKeyboardButton(f"📢 إشترك في {chan}", url=f"https://t.me/{clean_chan}"))
        markup.add(types.InlineKeyboardButton("✅ تم الاشتراك في الكل", callback_data="check_sub"))
        bot.send_message(message.chat.id, "⚠️ يجب عليك الاشتراك في القنوات أولاً لاستخدام البوت.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_callback(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التفعيل!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "شكراً لاشتراكك! اختر من القائمة:", reply_markup=main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات بعد!", show_alert=True)

@bot.message_handler(func=lambda message: message.text in ['📢 نشر إعلان بيع', '🔍 نشر طلب شراء', '🔄 طلب تبادل'])
def ask_details(message):
    if not is_subscribed(message.from_user.id):
        return start(message)
    
    user_data[message.chat.id] = {
        'type': message.text, 
        'text': '', 
        'photo': None, 
        'username': message.from_user.username or "مخفي", 
        'user_id': message.from_user.id
    }
    msg = bot.send_message(message.chat.id, f"📝 أرسل تفاصيل ({message.text}) الآن:")
    bot.register_next_step_handler(msg, get_text)

def get_text(message):
    if message.text in ['📢 نشر إعلان بيع', '🔍 نشر طلب شراء', '🔄 طلب تبادل', '/start']:
        bot.send_message(message.chat.id, "❌ تم إلغاء العملية السابقة، ابدأ من جديد.")
        return
        
    user_data[message.chat.id]['text'] = message.text
    msg = bot.send_message(message.chat.id, "📸 أرسل صورة للإعلان (أو ملف)، أو أرسل /skip للنشر بدون صورة:")
    bot.register_next_step_handler(msg, get_photo_or_skip)

def get_photo_or_skip(message):
    if message.content_type == 'photo':
        user_data[message.chat.id]['photo'] = message.photo[-1].file_id
        finish_ad(message)
    elif message.content_type == 'document': 
        user_data[message.chat.id]['photo'] = message.document.file_id
        finish_ad(message)
    elif message.text == '/skip':
        finish_ad(message)
    elif message.text == '/start':
        start(message)
    else:
        bot.send_message(message.chat.id, "⚠️ يرجى إرسال صورة أو ضغط /skip فقط.")
        bot.register_next_step_handler(message, get_photo_or_skip)

def finish_ad(message):
    data = user_data.get(message.chat.id)
    if not data: return 

    bot.send_message(message.chat.id, "✅ تم إرسال طلبك للإدارة للمراجعة.")
    
    caption = (f"🚨 **إعلان جديد للمراجعة**\n\n"
               f"📌 **النوع:** {data['type']}\n"
               f"📝 **التفاصيل:**\n{data['text']}\n\n"
               f"👤 **الناشر:** @{data['username']}\n"
               f"🆔 **الأيدي:** `{data['user_id']}`")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ قبول", callback_data=f"acc_{message.chat.id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"rej_{message.chat.id}")
    )
    
    if data['photo']:
        try:
            bot.send_photo(ADMIN_ID, data['photo'], caption=caption, reply_markup=markup, parse_mode="Markdown")
        except:
            bot.send_message(ADMIN_ID, caption + "\n\n(مرفق ملف أعلاه)", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(ADMIN_ID, caption, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("acc_", "rej_")))
def handle_ad(call):
    action, u_id = call.data.split('_')
    u_id = int(u_id)
    
    original_text = call.message.caption if call.message.content_type == 'photo' else call.message.text
    
    if action == "acc":
        chan_markup = types.InlineKeyboardMarkup()
        chan_markup.add(types.InlineKeyboardButton("💬 تواصل مع صاحب الإعلان", url=f"tg://user?id={u_id}"))
        
        final_msg = original_text.replace("🚨 إعلان جديد للمراجعة", "🌟 إعلان جديد 🌟")
        
        try:
            if call.message.content_type == 'photo':
                bot.send_photo(POST_CHANNEL, call.message.photo[-1].file_id, caption=final_msg, reply_markup=chan_markup, parse_mode="Markdown")
            else:
                bot.send_message(POST_CHANNEL, final_msg, reply_markup=chan_markup, parse_mode="Markdown")
            
            bot.send_message(u_id, "🎉 مبروك! تم قبول إعلانك ونشره في القناة.")
            bot.answer_callback_query(call.id, "✅ تم النشر بنجاح")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ خطأ في النشر: تأكد أن البوت أدمن", show_alert=True)
    
    elif action == "rej":
        try:
            bot.send_message(u_id, "❌ نعتذر منك، تم رفض إعلانك لمخالفته الشروط.")
        except: pass
        bot.answer_callback_query(call.id, "❌ تم الرفض")

    bot.delete_message(call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    print("🚀 البوت يعمل الآن بنظام الأيدي والقناتين والحماية...")
    bot.infinity_polling()
