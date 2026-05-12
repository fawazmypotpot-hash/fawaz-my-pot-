import os
from urllib.parse import quote, unquote
import yt_dlp as youtube_dl
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# ========== [ بياناتك ] ==========
TOKEN = "8777405946:AAGm4No4pGhMhy4-Cbc4Ojwo7UCDFpjCmxw"
CHANNEL_ID = "@ahmbyy123"
ADMIN_ID = 6322654752
SEP = "|||"
# =================================

# --- خيارات الجودة ---
QUALITY_OPTIONS = {
    "144": "144p", "360": "360p", "480": "480p",
    "720": "720p", "1080": "1080p"
}

# ========== [ اشتراك إجباري ] ==========
async def check_sub(uid, ctx):
    try:
        m = await ctx.bot.get_chat_member(CHANNEL_ID, uid)
        return m.status in ['member', 'administrator', 'creator']
    except:
        return False

# ========== [ أمر البداية ] ==========
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("🎯 أرسل رابط فيديو للتحميل.")

# ========== [ معالج الرسائل ] ==========
async def handle_msg(update: Update, context: CallbackContext):
    user = update.effective_user
    url = update.message.text.strip()

    # معالجة خاصة لفيسبوك
    if "facebook.com" in url or "fb.watch" in url or "fb.com" in url:
        await msg_download(update, context, url)
        return

    # 1. اشتراك إجباري
    if not await check_sub(user.id, context):
        kb = [[InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{CHANNEL_ID[1:]}")],
              [InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check_sub")]]
        await update.message.reply_text("⚠️ يجب عليك الاشتراك في قناتنا أولاً للمتابعة.", reply_markup=InlineKeyboardMarkup(kb))
        return

    # 2. عرض أزرار الجودة (باستخدام SEP الصحيح)
    kb, row = [], []
    for qid, qname in QUALITY_OPTIONS.items():
        row.append(InlineKeyboardButton(qname, callback_data=f"dl{SEP}{qid}{SEP}{quote(url, safe='')}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("🎵 تحميل الصوت", callback_data=f"aud{SEP}{quote(url, safe='')}")])
    await update.message.reply_text("🎬 اختر الجودة:", reply_markup=InlineKeyboardMarkup(kb))

# ========== [ معالج أزرار الجودة ] ==========
async def quality_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    parts = q.data.split(SEP)
    height_str = parts[1]
    url = unquote(parts[2])
    msg = q.message
    await msg.edit_text("⏳ جاري تحميل الفيديو...")
    await do_download(update, context, url, height_str)

# ========== [ معالج الصوت ] ==========
async def audio_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    url = unquote(q.data.split(SEP)[1])
    await q.edit_message_text("⏳ جاري تحميل الصوت...")
    await do_download(update, context, url, audio_only=True)

# ========== [ دالة التحميل النهائية (للمنصات التي تستخدم أزرار) ] ==========
async def do_download(update: Update, context: CallbackContext, url: str, height_str=None, audio_only=False):
    q = update.callback_query
    msg = await q.message.reply_text("⏳ جاري التحميل...")
    fname = None
    try:
        if audio_only:
            format_str = "bestaudio/best"
        elif height_str and height_str.isdigit():
            format_str = f"bestvideo[height<={height_str}]+bestaudio/best[height<={height_str}]"
        else:
            format_str = "best"

        ydl_opts = {
            'format': format_str,
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if audio_only else []
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            if audio_only:
                fname = fname.rsplit('.', 1)[0] + '.mp3'

            await msg.edit_text("⬆️ جاري الرفع...")
            if audio_only:
                with open(fname, 'rb') as f:
                    await q.message.reply_audio(f, title=info.get('title', 'Audio'))
            else:
                with open(fname, 'rb') as f:
                    await q.message.reply_video(f, caption=f"🎬 {info.get('title', 'Video')}")
            await msg.delete()
    except Exception as e:
        try:
            await msg.edit_text("🔄 جاري محاولة تحميل الصيغة العامة...")
            ydl_opts['format'] = 'best'
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                fname = ydl.prepare_filename(info)
                if audio_only:
                    fname = fname.rsplit('.', 1)[0] + '.mp3'

                await msg.edit_text("⬆️ جاري الرفع...")
                if audio_only:
                    with open(fname, 'rb') as f:
                        await q.message.reply_audio(f, title=info.get('title', 'Audio'))
                else:
                    with open(fname, 'rb') as f:
                        await q.message.reply_video(f, caption=f"🎬 {info.get('title', 'Video')}")
                await msg.delete()
        except Exception as e2:
            await msg.edit_text(f"❌ خطأ: {e2}")
    finally:
        if fname and os.path.exists(fname):
            os.remove(fname)

# ========== [ تحميل من رسالة مباشرة (للمنصات التي لا تحتاج أزرار جودة) ] ==========
async def msg_download(update: Update, context: CallbackContext, url: str, height_str=None, audio_only=False):
    """تحميل مباشر من رسالة نصية (يُستخدم لفيسبوك وغيره)"""
    msg = await update.message.reply_text("⏳ جاري التحميل...")
    fname = None
    try:
        if audio_only:
            format_str = "bestaudio/best"
        elif height_str and height_str.isdigit():
            format_str = f"bestvideo[height<={height_str}]+bestaudio/best[height<={height_str}]"
        else:
            format_str = "bestvideo[height<=360]+bestaudio/best[height<=360]/best[height<=360]"

        ydl_opts = {
            'format': format_str,
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if audio_only else []
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            if audio_only:
                fname = fname.rsplit('.', 1)[0] + '.mp3'

            # فحص حجم الملف قبل الرفع
            file_size = os.path.getsize(fname)
            if file_size > 45 * 1024 * 1024:  # أكبر من 45 ميجابايت
                await msg.edit_text("❌ حجم الفيديو كبير جداً (أكبر من 45 ميجابايت). لا يمكن إرساله عبر تيليجرام.")
                os.remove(fname)
                return

            await msg.edit_text("⬆️ جاري الرفع...")
            if audio_only:
                with open(fname, 'rb') as f:
                    await update.message.reply_audio(f, title=info.get('title', 'Audio'))
            else:
                with open(fname, 'rb') as f:
                    await update.message.reply_video(f, caption=f"🎬 {info.get('title', 'Video')}")
            await msg.delete()
    except Exception as e:
        try:
            await msg.edit_text("🔄 جاري محاولة تحميل الصيغة العامة...")
            ydl_opts['format'] = 'best'
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                fname = ydl.prepare_filename(info)
                if audio_only: fname = fname.rsplit('.', 1)[0] + '.mp3'
                await msg.edit_text("⬆️ جاري الرفع...")
                if audio_only:
                    with open(fname, 'rb') as f:
                        await update.message.reply_audio(f, title=info.get('title', 'Audio'))
                else:
                    with open(fname, 'rb') as f:
                        await update.message.reply_video(f, caption=f"🎬 {info.get('title', 'Video')}")
                await msg.delete()
        except Exception as e2:
            await msg.edit_text(f"❌ خطأ: {e2}")
    finally:
        if fname and os.path.exists(fname):
            os.remove(fname)

# ========== [ زر التحقق من الاشتراك ] ==========
async def check_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    if await check_sub(q.from_user.id, context):
        await q.edit_message_text("✅ تم التحقق من اشتراكك. أرسل رابط الفيديو الآن.")
    else:
        await q.answer("❌ لم يتم التحقق من اشتراكك بعد.", show_alert=True)

# ========== [ الدالة الرئيسية ] ==========
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(quality_callback, pattern=rf"^dl\{SEP}"))
    app.add_handler(CallbackQueryHandler(audio_callback, pattern=rf"^aud\{SEP}"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("✅ البوت الجديد يعمل!")
    app.run_polling()

if __name__ == "__main__":
    main()