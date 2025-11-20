from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import Database
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

# --- دوال مساعدة ---
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 رصيدي", callback_data='balance'),
         InlineKeyboardButton("📊 إحصائياتي", callback_data='stats')],
        [InlineKeyboardButton("📋 المهام", callback_data='tasks'),
         InlineKeyboardButton("📺 مشاهدة إعلان", callback_data='watch_ad')],
        [InlineKeyboardButton("🔗 رابط الإحالة", callback_data='referral'),
         InlineKeyboardButton("💸 سحب الأرباح", callback_data='withdraw')],
        [InlineKeyboardButton("ℹ️ معلومات", callback_data='info')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text="👋 القائمة الرئيسية:"):
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=get_main_keyboard())

# --- معالجات الأوامر ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    referrer_id = None
    
    if args and args[0].startswith('ref_'):
        try:
            referrer_id = int(args[0].replace('ref_', ''))
            if referrer_id == user.id:
                referrer_id = None
        except:
            pass
    
    user_data = db.get_or_create_user(user.id, user.username, user.first_name, referrer_id)
    
    welcome_text = f"""
🎉 أهلاً بك في بوت الأرباح الاحترافي!

💎 اربح نقاط من خلال:
• مشاهدة الإعلانات
• الانضمام للقنوات
• دعوة الأصدقاء

💵 حوّل نقاطك إلى USDT حقيقي!

📈 رصيدك الحالي: {user_data['points']} نقطة
💰 = {user_data['points'] / Config.POINTS_TO_USDT_RATE:.2f} USDT
"""
    if referrer_id:
        welcome_text += f"\n🎁 لقد حصلت على {Config.REFERRAL_BONUS_LEVEL1} نقطة كمكافأة ترحيبية!"
    
    await send_main_menu(update, context, welcome_text)

# --- الأزرار الأساسية ---
async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = db.get_user(query.from_user.id)
    usdt_value = user['points'] / Config.POINTS_TO_USDT_RATE
    
    text = f"""
💰 **رصيدك الحالي:**

🪙 نقاط: **{user['points']:,}**
💵 USDT: **${usdt_value:.2f}**
👥 إحالاتك: {user['referral_count']}
📊 إجمالي الأرباح: {user['total_earned']:,} نقطة
"""
    keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = db.get_user(query.from_user.id)
    stats = db.get_user_stats(query.from_user.id)
    
    text = f"""
📊 **إحصائياتك الشاملة:**

👁️ إعلانات تم مشاهدتها: {stats.get('total_ad_views',0)}
📢 قنوات انضممت لها: {stats.get('total_channel_joins',0)}
👥 إحالاتك: {user['referral_count']}
💰 إجمالي نقاط المهام: {stats.get('total_from_tasks',0)}
"""
    keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = db.get_user(query.from_user.id)
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user['user_id']}"
    
    text = f"""
🔗 **رابط الإحالة الخاص بك:**
`{referral_link}`

🎁 مكافآت الإحالة:
• المستوى 1: {Config.REFERRAL_BONUS_LEVEL1} نقطة
• المستوى 2: {Config.REFERRAL_BONUS_LEVEL2} نقطة
"""
    keyboard = [
        [InlineKeyboardButton("📤 مشاركة الرابط", url=f"https://t.me/share/url?url={referral_link}")],
        [InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = f"""
ℹ️ معلومات عن البوت:

💎 اربح نقاط بمشاهدة الإعلانات والانضمام للقنوات ودعوة الأصدقاء
💵 {Config.POINTS_TO_USDT_RATE} نقطة = 1 USDT
💰 الحد الأدنى للسحب: {Config.MIN_WITHDRAWAL} USDT
"""
    keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- مشاهدة إعلان (وظيفة تجريبية) ---
async def watch_ad_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # إضافة نقاط مشاهدة إعلان
    db.add_points(query.from_user.id, Config.POINTS_PER_AD_VIEW, task_type='ad_view', task_id='ad_1')
    
    text = f"🎉 شاهدت إعلانًا وحصلت على {Config.POINTS_PER_AD_VIEW} نقطة!"
    keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- طلب سحب ---
async def withdraw_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = db.get_user(query.from_user.id)
    if user['points'] < Config.MIN_WITHDRAWAL * Config.POINTS_TO_USDT_RATE:
        text = f"⚠️ رصيدك أقل من الحد الأدنى للسحب ({Config.MIN_WITHDRAWAL} USDT)."
        keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # سحب تجريبي: استخدام محفظة USDT من .env
    withdrawal_id = db.create_withdrawal(user['user_id'], Config.MIN_WITHDRAWAL, Config.USDT_WALLET)
    if withdrawal_id:
        text = f"✅ تم إنشاء طلب السحب بنجاح! (ID: {withdrawal_id})"
    else:
        text = "❌ حدث خطأ أثناء إنشاء طلب السحب."
    
    keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await send_main_menu(update, context)

# --- التشغيل ---
def main():
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # أوامر
    application.add_handler(CommandHandler("start", start_command))
    
    # أزرار
    application.add_handler(CallbackQueryHandler(balance_handler, pattern='^balance$'))
    application.add_handler(CallbackQueryHandler(stats_handler, pattern='^stats$'))
    application.add_handler(CallbackQueryHandler(referral_handler, pattern='^referral$'))
    application.add_handler(CallbackQueryHandler(info_handler, pattern='^info$'))
    application.add_handler(CallbackQueryHandler(main_menu_handler, pattern='^main_menu$'))
    application.add_handler(CallbackQueryHandler(watch_ad_handler, pattern='^watch_ad$'))
    application.add_handler(CallbackQueryHandler(withdraw_handler, pattern='^withdraw$'))
    
    logger.info("🚀 البوت بدأ العمل...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
