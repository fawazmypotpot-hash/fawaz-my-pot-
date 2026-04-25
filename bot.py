# -*- coding: utf-8 -*-
import os, json, logging
import yt_dlp as youtube_dl
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# ========== [ الإعدادات - ضع بياناتك هنا ] ==========
TOKEN = "8687541181:AAFQJLrMUhIRZE8zZnV9-Wkatn5-WFtgZls"                # ضع توكن البوت هنا
CHANNEL_ID = "@ahmbyy123"      # ضع معرف قناتك هنا
ADMIN_ID =6322654752                  # ضع معرفك الرقمي هنا
# ===================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- دوال الأزرار ---
def load_buttons():
    try:
        with open('buttons.json', 'r') as f: return json.load(f)
    except: return []

def save_buttons(buttons):
    with open('buttons.json', 'w') as f: json.dump(buttons, f)

# --- اشتراك إجباري ---
async def check_sub(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- الأوامر ---
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("مرحباً! أرسل رابط الفيديو للتحميل.")

async def menu(update: Update, context: CallbackContext):
    btns = load_buttons()
    if not btns:
        await update.message.reply_text("لا توجد أزرار.")
        return
    kb = [[InlineKeyboardButton(b['name'], callback_data=f"btn_{b['id']}")] for b in btns]
    await update.message.reply_text("اختر:", reply_markup=InlineKeyboardMarkup(kb))

async def admin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID: return
    kb = [[InlineKeyboardButton("➕ زر جديد", callback_data="new_btn")]]
    await update.message.reply_text("لوحة التحكم:", reply_markup=InlineKeyboardMarkup(kb))

# --- التحميل ---
async def handle_msg(update: Update, context: CallbackContext):
    user = update.effective_user
    if not await check_sub(user.id, context):
        kb = [[InlineKeyboardButton("اشترك", url=f"https://t.me/{CHANNEL_ID[1:]}")],
              [InlineKeyboardButton("تحققت", callback_data="check_sub")]]
        await update.message.reply_text("اشترك أولاً:", reply_markup=InlineKeyboardMarkup(kb))
        return
    url = update.message.text
    msg = await update.message.reply_text("⏳ جاري التحميل...")
    try:
        ydl_opts = {'format': 'mp4', 'outtmpl': '%(title)s.%(ext)s', 'quiet': True, 'noplaylist': True}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            await msg.edit_text("⬆️ جاري الرفع...")
            with open(fname, 'rb') as f:
                await update.message.reply_video(f, caption=f"🎬 {info['title']}")
            os.remove(fname)
            await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {e}")

# --- نظام الأزرار ---
async def new_btn(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("أرسل اسم الزر:")
    context.user_data['step'] = 'name'

async def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text
    step = context.user_data.get('step')
    if step:
        if step == 'name':
            context.user_data['name'] = text
            kb = [[InlineKeyboardButton("رابط", callback_data="type_url")],
                  [InlineKeyboardButton("رسالة", callback_data="type_msg")]]
            await update.message.reply_text("اختر النوع:", reply_markup=InlineKeyboardMarkup(kb))
            context.user_data['step'] = 'type'
        elif step == 'content':
            btns = load_buttons()
            btns.append({"id": len(btns)+1, "name": context.user_data['name'],
                         "type": context.user_data['type'], "content": text})
            save_buttons(btns)
            await update.message.reply_text("✅ تم إنشاء الزر!")
            context.user_data.clear()
        return
    if not await check_sub(user.id, context):
        kb = [[InlineKeyboardButton("اشترك", url=f"https://t.me/{CHANNEL_ID[1:]}")],
              [InlineKeyboardButton("تحققت", callback_data="check_sub")]]
        await update.message.reply_text("اشترك أولاً:", reply_markup=InlineKeyboardMarkup(kb))
        return
    await handle_msg(update, context)

async def btn_type(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    context.user_data['type'] = q.data
    await q.edit_message_text("أرسل المحتوى (رابط أو نص):")
    context.user_data['step'] = 'content'

async def btn_click(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    bid = int(q.data.split('_')[1])
    btn = next((b for b in load_buttons() if b['id'] == bid), None)
    if btn:
        await q.edit_message_text(btn['content'])

async def check_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    if await check_sub(q.from_user.id, context):
        await q.edit_message_text("✅ تم التحقق. أرسل الرابط.")
    else:
        await q.answer("لم تشترك بعد!", show_alert=True)

# --- التشغيل ---
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(new_btn, pattern="^new_btn$"))
    app.add_handler(CallbackQueryHandler(btn_type, pattern="^type_"))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(btn_click, pattern="^btn_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ البوت يعمل!")
    app.run_polling()

if __name__ == "__main__":
    main()

