import collections
if not hasattr(collections, 'MutableMapping'):
    import collections.abc
    collections.MutableMapping = collections.abc.MutableMapping
    collections.Mapping = collections.abc.Mapping
    collections.Callable = collections.abc.Callable

import telebot
from telebot import types
import os

# --- الإعدادات ---
API_TOKEN = '8536497984:AAFreSUHUUp12w_SNs2WH1RQO3KNcBhqmyk'
ADMIN_ID = 6671521979 
POST_CHANNEL_ID = '@BB_VBN' 
CHANNELS = ['@BB_VBN', '@VPN_Dzz'] 

bot = telebot.TeleBot(API_TOKEN)
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
        bot.send_message(message.chat.id, "مرحباً بك في سوق الخدمات 💎\nتم التحديث والتشغيل بنجاح!", reply_markup=main_keyboard())
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
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "شكراً لاشتراكك! اختر من القائمة:", reply_markup=main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد في القنوات!", show_alert=True)

@bot.message_handler(func=lambda message: message.text in ['📢 نشر إعلان بيع', '🔍 نشر طلب شراء', '🔄 طلب تبادل'])
def ask_details(message):
    if not is_subscribed(message.from_user.id): return start(message)
    user_data[message.chat.id] = {'type': message.text, 'text': '', 'photo': None, 'user_id': message.from_user.id, 'username': message.from_user.username}
    msg = bot.send_message(message.chat.id, f"📝 أرسل تفاصيل ({message.text}) الآن:")
    bot.register_next_step_handler(msg, get_text)

def get_text(message):
    if not message.text or message.text.startswith('/'):
        bot.send_message(message.chat.id, "⚠️ يرجى إرسال نص الإعلان بشكل صحيح.")
        return
    user_data[message.chat.id]['text'] = message.text
    msg = bot.send_message(message.chat.id, "📸 أرسل صورة للإعلان، أو أرسل /skip للنشر بدون صورة:")
    bot.register_next_step_handler(msg, get_photo_or_skip)

def get_photo_or_skip(message):
    if message.content_type == 'photo':
        user_data[message.chat.id]['photo'] = message.photo[-1].file_id
    finish_ad(message)

def finish_ad(message):
    data = user_data.get(message.chat.id)
    if not data: return
    
    bot.send_message(message.chat.id, "✅ تم إرسال طلبك للإدارة للمراجعة.")
    
    # تنسيق الرسالة التي تصل للأدمن مع الأيدي
    caption = (f"🚨 **طلب جديد**\n\n"
               f"📌 النوع: {data['type']}\n"
               f"👤 الناشر: @{data.get('username', 'مخفي')}\n"
               f"🆔 الأيدي: `{data['user_id']}`\n"
               f"📝 النص:\n{data['text']}")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ قبول ونشر", callback_data=f"acc_{message.chat.id}"),
               types.InlineKeyboardButton("❌ رفض", callback_data=f"rej_{message.chat.id}"))
    
    if data['photo']:
        bot.send_photo(ADMIN_ID, data['photo'], caption=caption, reply_markup=markup, parse_mode='Markdown')
    else:
        bot.send_message(ADMIN_ID, caption, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith(("acc_", "rej_")))
def handle_ad(call):
    action, u_id = call.data.split('_')
    u_id = int(u_id)
    
    if action == "acc":
        original_msg = call.message
        # استخراج النص من الكابشن أو الرسالة النصية
        info_text = original_msg.caption if original_msg.content_type == 'photo' else original_msg.text
        
        # تجهيز النص النهائي للقناة
        clean_text = info_text.replace("🚨 **طلب جديد**", "✨ **إعلان معتمد** ✨")
        warning = "\n\n⚠️ **الإدارة غير مسؤولة عن أي تعامل خارج البوت.**"
        final_post = clean_text + warning
        
        try:
            if original_msg.content_type == 'photo':
                bot.send_photo(POST_CHANNEL_ID, original_msg.photo[-1].file_id, caption=final_post, parse_mode='Markdown')
            else:
                bot.send_message(POST_CHANNEL_ID, final_post, parse_mode='Markdown')
            bot.send_message(u_id, "🎉 مبروك! تم قبول إعلانك ونشره في القناة.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ خطأ في النشر: تأكد أن البوت مشرف في القناة.\n{e}")
            
    elif action == "rej":
        bot.send_message(u_id, "❌ نعتذر، تم رفض طلبك من قبل الإدارة.")

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
