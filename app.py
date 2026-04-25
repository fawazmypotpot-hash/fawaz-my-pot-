import os, json, logging
import yt_dlp as youtube_dl
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# --- المتغيرات ستُقرأ من إعدادات FPS.ms ---
TOKEN = os.environ.get('8687541181:AAFQJLrMUhIRZE8zZnV9-Wkatn5-WFtgZls')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '@ahmbyy123')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '6322654752'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def load_buttons():
    try:
        with open('buttons.json', 'r') as f: return json.load(f)
    except: return []
def save_buttons(b): 
    with open('buttons.json', 'w') as f: json.dump(b, f)

async def check_sub(uid, ctx):
    try:
        m = await ctx.bot.get_chat_member(CHANNEL_ID, uid)
        return m.status in ['member', 'administrator', 'creator']
    except: return False

async def start(u, c): await u.message.reply_text("مرحباً! أرسل رابط الفيديو للتحميل.")
async def menu(u, c):
    btns = load_buttons()
    if not btns: await u.message.reply_text("لا توجد أزرار."); return
    kb = [[InlineKeyboardButton(b['name'], callback_data=f"btn_{b['id']}")] for b in btns]
    await u.message.reply_text("اختر:", reply_markup=InlineKeyboardMarkup(kb))
async def admin(u, c):
    if u.effective_user.id != ADMIN_ID: return
    await u.message.reply_text("لوحة التحكم:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ زر جديد", callback_data="new_btn")]]))

async def handle_msg(u, c):
    if not await check_sub(u.effective_user.id, c):
        kb = [[InlineKeyboardButton("اشترك", url=f"https://t.me/{CHANNEL_ID[1:]}")], [InlineKeyboardButton("تحققت", callback_data="check_sub")]]
        await u.message.reply_text("اشترك أولاً:", reply_markup=InlineKeyboardMarkup(kb)); return
    url = u.message.text
    msg = await u.message.reply_text("⏳ جاري التحميل...")
    try:
        with youtube_dl.YoutubeDL({'format': 'mp4', 'outtmpl': '%(title)s.%(ext)s', 'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            await msg.edit_text("⬆️ جاري الرفع...")
            with open(fname, 'rb') as f: await u.message.reply_video(f, caption=f"🎬 {info['title']}")
            os.remove(fname); await msg.delete()
    except Exception as e: await msg.edit_text(f"❌ خطأ: {e}")

async def new_btn(u, c):
    await u.callback_query.answer(); await u.callback_query.edit_message_text("أرسل اسم الزر:")
    c.user_data['step'] = 'name'
async def handle_message(u, c):
    txt = u.message.text; step = c.user_data.get('step')
    if step:
        if step == 'name':
            c.user_data['name'] = txt
            kb = [[InlineKeyboardButton("رابط", callback_data="type_url")], [InlineKeyboardButton("رسالة", callback_data="type_msg")]]
            await u.message.reply_text("اختر النوع:", reply_markup=InlineKeyboardMarkup(kb)); c.user_data['step'] = 'type'
        elif step == 'content':
            btns = load_buttons(); btns.append({"id": len(btns)+1, "name": c.user_data['name'], "type": c.user_data['type'], "content": txt})
            save_buttons(btns); await u.message.reply_text("✅ تم إنشاء الزر!"); c.user_data.clear()
        return
    if not await check_sub(u.effective_user.id, c):
        kb = [[InlineKeyboardButton("اشترك", url=f"https://t.me/{CHANNEL_ID[1:]}")], [InlineKeyboardButton("تحققت", callback_data="check_sub")]]
        await u.message.reply_text("اشترك أولاً:", reply_markup=InlineKeyboardMarkup(kb)); return
    await handle_msg(u, c)

async def btn_type(u, c):
    q = u.callback_query; await q.answer(); c.user_data['type'] = q.data
    await q.edit_message_text("أرسل المحتوى (رابط أو نص):"); c.user_data['step'] = 'content'
async def btn_click(u, c):
    q = u.callback_query; await q.answer(); bid = int(q.data.split('_')[1])
    btn = next((b for b in load_buttons() if b['id'] == bid), None)
    if btn: await q.edit_message_text(btn['content'])
async def check_callback(u, c):
    q = u.callback_query; await q.answer()
    if await check_sub(q.from_user.id, c): await q.edit_message_text("✅ تم التحقق. أرسل الرابط.")
    else: await q.answer("لم تشترك بعد!", show_alert=True)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(new_btn, pattern="^new_btn$"))
    app.add_handler(CallbackQueryHandler(btn_type, pattern="^type_"))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(btn_click, pattern="^btn_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ البوت يعمل!"); app.run_polling()

if __name__ == "__main__":
    main()
