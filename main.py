import telebot # تصحيح حرف الـ I
from telebot import types
import time

# --- الإعدادات ---
# تأكد من تغيير التوكن من BotFather إذا قمت بنشر الكود علناً
API_TOKEN = '8536497984:AAFreSUHUUp12w_SNs2WH1RQO3KNcBhqmyk'
ADMIN_ID = 6671521979 
POST_CHANNEL_ID = '@BB_VBN' 
CHANNELS = ['@BB_VBN', '@VPN_Dzz'] 

bot = telebot.TeleBot(API_TOKEN)

# دالة فحص الاشتراك
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
    if is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "مرحباً بك في سوق الخدمات 💎", reply_markup=main_keyboard())
    else:
        markup = types.InlineKeyboardMarkup()
        for chan in CHANNELS:
            clean_chan = chan.replace('@', '')
            markup.add(types.InlineKeyboardButton(f"📢 إشترك في {chan}", url=f"https://t.me/{clean_chan}"))
        markup.add(types.InlineKeyboardButton("✅ تم الاشتراك", callback_data="check_sub"))
        bot.send_message(message.chat.id, "⚠️ يجب عليك الاشتراك في القنوات أولاً لاستخدام البوت.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "✅ تم التفعيل بنجاح!", reply_markup=main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات بعد!", show_alert=True)

@bot.message_handler(func=lambda message: message.text in ['📢 نشر إعلان بيع', '🔍 نشر طلب شراء', '🔄 طلب تبادل'])
def handle_publish(message):
    if not is_subscribed(message.from_user.id): 
        return start(message)
    msg = bot.send_message(message.chat.id, f"📝 أرسل الآن تفاصيل ({message.text}):\n(يمكنك إرسال نص أو صورة مع وصف)")
    bot.register_next_step_handler(msg, process_ad, message.text)

def process_ad(message, ad_type):
    # إعداد معلومات الناشر
    user_info = f"\n\n👤 الناشر: @{message.from_user.username or 'مخفي'}\n🆔 الأيدي: `{message.from_user.id}`"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ قبول", callback_data=f"acc_{message.from_user.id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"rej_{message.from_user.id}")
    )

    try:
        if message.content_type == 'photo':
            caption = f"✨ **{ad_type}** ✨\n\n{message.caption or ''}{user_info}"
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode='Markdown')
        else:
            text = f"✨ **{ad_type}** ✨\n\n{message.text}{user_info}"
            bot.send_message(ADMIN_ID, text, reply_markup=markup, parse_mode='Markdown')
        
        bot.send_message(message.chat.id, "✅ تم إرسال طلبك للإدارة، سيتم نشره فور الموافقة.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء إرسال طلبك للإدارة.")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("acc_", "rej_")))
def handle_admin_action(call):
    action, u_id = call.data.split('_')
    
    if action == "acc":
        warning = "\n\n⚠️ **الإدارة غير مسؤولة عن أي تعامل خارج البوت.**"
        try:
            if call.message.content_type == 'photo':
                bot.send_photo(POST_CHANNEL_ID, call.message.photo[-1].file_id, caption=call.message.caption + warning, parse_mode='Markdown')
            else:
                bot.send_message(POST_CHANNEL_ID, call.message.text + warning, parse_mode='Markdown')
            
            bot.send_message(int(u_id), "🎉 مبروك! وافقت الإدارة على إعلانك وتم نشره في القناة.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ فشل النشر في القناة: {e}")
            
    else:
        try:
            bot.send_message(int(u_id), "❌ نعتذر، تم رفض إعلانك من قبل الإدارة.")
        except: pass

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

if __name__ == "__main__":
    print("Bot is starting...")
    # استخدام infinity_polling لضمان استمرار البوت في العمل عند حدوث أخطاء بسيطة
    bot.infinity_polling(skip_pending=True)
