import os
import re
import urllib.request
import json
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

def clean_tiktok_url(url):
    """تنظيف رابط تيك توك من معلمات التتبع غير الضرورية"""
    match = re.search(r'tiktok\.com/@([^/]+)/video/(\d+)', url)
    if match:
        username = match.group(1)
        video_id = match.group(2)
        return f'https://www.tiktok.com/@{username}/video/{video_id}'
    return url

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

# ========== [ تحميل مباشر لفيسبوك ] ==========
async def fb_direct(update: Update, context: CallbackContext, url: str):
    """تحميل مباشر لفيسبوك مع محاولات متعددة لتفادي الحجم الكبير"""
    msg = await update.message.reply_text("⏳ جاري تحميل الفيديو من فيسبوك...")
    fname = None
    format_list = [
        "best[filesize<45M]",
        "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "best[height<=360]",
        "best",
        "worst[filesize<45M]",
        "bestvideo[height<=144]+bestaudio/best[height<=144]",
        "worst",
    ]
    for fmt in format_list:
        try:
            ydl_opts = {
                'format': fmt,
                'outtmpl': '%(title)s.%(ext)s',
                'quiet': True,
                'noplaylist': True,
                'merge_output_format': 'mp4',
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                fname = ydl.prepare_filename(info)
            if os.path.getsize(fname) <= 45 * 1024 * 1024:
                break
            else:
                os.remove(fname)
                fname = None
                await msg.edit_text(f"🔄 الجودة عالية جداً، جاري محاولة صيغة أصغر...")
        except Exception:
            continue

    if not fname:
        await msg.edit_text("❌ لم نتمكن من تحميل الفيديو بحجم مناسب. جرب رابطاً آخر.")
        return

    await msg.edit_text("⬆️ جاري الرفع...")
    with open(fname, 'rb') as f:
        await update.message.reply_video(f, caption=f"🎬 {info.get('title', 'Video')}")
    await msg.delete()
    if fname and os.path.exists(fname):
        os.remove(fname)

# ========== [ تحميل تيك توك ] ==========
async def tiktok_download(update: Update, context: CallbackContext, url: str, height_str=None, audio_only=False):
    """تحميل من تيك توك - يجرّب الصيغة الأولى ثم best مع تشخيص الأخطاء"""
    q = update.callback_query
    msg = await q.message.reply_text("⏳ جاري تحميل الفيديو من تيك توك...")
    fname = None
    last_error = ""
    for fmt in ('0', 'best', 'all'):
        try:
            ydl_opts = {
                'format': fmt,
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
            break
        except Exception as e:
            last_error = str(e)
            continue

    if not fname:
        await msg.edit_text(f"❌ فشل التحميل: {last_error}")
        return

    # فحص حجم الملف قبل محاولة الرفع
    file_size = os.path.getsize(fname)
    if file_size > 45 * 1024 * 1024:  # أكبر من 45 ميغابايت
        await msg.edit_text(
            f"❌ حجم الفيديو كبير جداً ({file_size / (1024*1024):.1f} ميغابايت). الحد الأقصى هو 50 ميغابايت.\n"
            "جرب تحميل فيديو أقصر أو بجودة أقل."
        )
        os.remove(fname)
        return

    try:
        await msg.edit_text("⬆️ جاري الرفع...")
        with open(fname, 'rb') as f:
            await update.message.reply_video(f, caption=f"🎬 {info.get('title', 'Video')}")
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ خطأ في الرفع: {e}")
    finally:
        if fname and os.path.exists(fname):
            os.remove(fname)

# ========== [ دالة التحميل العامة (يوتيوب وغيره) ] ==========
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
            await msg.edit_text("🔄 صيغة غير متوفرة، جاري تحميل الصيغة العامة...")
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

# ========== [ تحميل مباشر لروابط تيك توك الطويلة ] ==========
async def tiktok_direct(update: Update, context: CallbackContext, url: str):
    """تحميل مباشر لتيك توك مع إرسال عبر API مباشرة"""
    url = clean_tiktok_url(url)
    msg = await update.message.reply_text("⏳ جاري التحميل...")
    fname = None

    format_list = [
        "best[filesize<45M]",
        "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "best[height<=360]",
        "best",
        "worst[filesize<45M]",
        "worst",
    ]

    for fmt in format_list:
        try:
            ydl_opts = {
                'format': fmt,
                'outtmpl': '%(title)s.%(ext)s',
                'quiet': True,
                'noplaylist': True,
                'merge_output_format': 'mp4',
                'http_headers': {'User-Agent': 'Mozilla/5.0'},
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                fname = ydl.prepare_filename(info)

            if os.path.getsize(fname) <= 45 * 1024 * 1024:
                break
            else:
                os.remove(fname)
                fname = None
                await msg.edit_text("🔄 جاري تجربة صيغة أصغر...")
        except Exception:
            continue

    if not fname:
        await msg.edit_text("❌ فشل التحميل.")
        return

    # إرسال مباشر إلى API تيليجرام (الطريقة الناجحة)
    try:
        await msg.edit_text("⬆️ جاري الإرسال...")
        api_url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
        boundary = '----Boundary7MA4YWxkTrZu0gW'
        with open(fname, 'rb') as f:
            file_data = f.read()

        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{update.message.chat_id}\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="video"; filename="{os.path.basename(fname)}"\r\n'
            f'Content-Type: video/mp4\r\n\r\n'
        ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

        req = urllib.request.Request(api_url, data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
        with urllib.request.urlopen(req) as resp:
            result = json.load(resp)
            if result.get('ok'):
                await msg.edit_text("✅ تم إرسال الفيديو!")
            else:
                await msg.edit_text(f"❌ فشل: {result.get('description')}")
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {e}")
    finally:
        if fname and os.path.exists(fname):
            os.remove(fname)

async def youtube_direct(update: Update, context: CallbackContext, url: str):
    context.user_data['last_url'] = url
    kb, row = [], []
    for qid, qname in QUALITY_OPTIONS.items():
        row.append(InlineKeyboardButton(qname, callback_data=f"dl{SEP}{qid}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("🎵 صوت فقط", callback_data=f"aud{SEP}")])
    await update.message.reply_text("🎬 اختر الجودة:", reply_markup=InlineKeyboardMarkup(kb))
# ========== [ معالج الرسائل ] ==========
async def handle_msg(update: Update, context: CallbackContext):
    user = update.effective_user
    url = update.message.text.strip()
    if "tiktok.com" in url:
        url = clean_tiktok_url(url)

    # 1. اشتراك إجباري
    if not await check_sub(user.id, context):
        kb = [[InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{CHANNEL_ID[1:]}")],
              [InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check_sub")]]
        await update.message.reply_text("⚠️ اشترك أولاً:", reply_markup=InlineKeyboardMarkup(kb))
        return

    # 2. معالجة فيسبوك مباشرة
    if "facebook.com" in url or "fb.watch" in url or "fb.com" in url:
        await fb_direct(update, context, url)
        return

    # معالجة تيك توك مباشرة لأي رابط تيك توك
    if "tiktok.com" in url:
        await tiktok_direct(update, context, url)
        return

    # معالجة يوتيوب مباشرة
    if "youtube.com" in url or "youtu.be" in url:
        await youtube_direct(update, context, url)
        return

    # 3. عرض أزرار الجودة للمنصات الأخرى
    kb, row = [], []
    for qid, qname in QUALITY_OPTIONS.items():
        row.append(InlineKeyboardButton(qname, callback_data=f"dl{SEP}{qid}{SEP}{quote(url, safe='')}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("🎵 صوت فقط", callback_data=f"aud{SEP}{quote(url, safe='')}")])
    await update.message.reply_text("🎬 اختر الجودة:", reply_markup=InlineKeyboardMarkup(kb))

# ========== [ معالج أزرار الجودة ] ==========
async def quality_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    parts = q.data.split(SEP)
    
    # --- معالجة أزرار يوتيوب المختصرة (بدون رابط) ---
    if len(parts) == 2:
        url = context.user_data.get('last_url', '')
        if "youtube.com" in url or "youtu.be" in url:
            height_str = parts[1]
            await q.edit_message_text("⏳ جاري التحميل...")
            await do_download(update, context, url, height_str)
            return
        else:
            # إذا كانت الصيغة مختصرة ولكن الرابط ليس يوتيوب، نتجاهل
            await q.answer("حدث خطأ، أعد إرسال الرابط.")
            return
    
    # --- المعالجة العادية (لغير يوتيوب) ---
    height_str = parts[1]
    url = unquote(parts[2])
    if "tiktok.com" in url:
        url = clean_tiktok_url(url)
    if "tiktok.com" in url:
        await tiktok_download(update, context, url, height_str)
    else:
        await do_download(update, context, url, height_str)
# ========== [ معالج الصوت ] ==========
async def audio_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    url = unquote(q.data.split(SEP)[1])
    if "tiktok.com" in url:
        await tiktok_download(update, context, url, audio_only=True)
    else:
        await do_download(update, context, url, audio_only=True)

# ========== [ زر التحقق من الاشتراك ] ==========
async def check_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    if await check_sub(q.from_user.id, context):
        await q.edit_message_text("✅ تم التحقق. أرسل رابط الفيديو.")
    else:
        await q.answer("❌ لم تشترك بعد!", show_alert=True)

# ========== [ الدالة الرئيسية ] ==========
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(quality_callback, pattern=rf"^dl\{SEP}"))
    app.add_handler(CallbackQueryHandler(audio_callback, pattern=rf"^aud\{SEP}"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("✅ بوت التحميل يعمل!")
    app.run_polling()

if __name__ == "__main__":
    main()