import os, json, logging, datetime, asyncio
from urllib.parse import quote, unquote
import yt_dlp as youtube_dl
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, ConversationHandler

AWAITING_CHANNEL, SEARCH_QUERY, PLAY_COUNT, GIF_CONVERT, BROADCAST_MSG = range(5)

TOKEN = os.environ.get('BOT_TOKEN', '8687541181:AAGImfmybwuBWOoH6BtxSVtSOD8zfquQ4-A')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '@ahmbyy123')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '6322654752'))

CUSTOM_BUTTONS = [
    {"name": "📢 قناتنا", "type": "url", "content": "https://t.me/ahmbyy123"},
    {"name": "💬 تواصل معنا", "type": "url", "content": "https://t.me/aboabedd9"},
    {"name": "📰 آخر الأخبار", "type": "message", "content": "مرحباً! آخر أخبار البوت:\n- أزرار مخصصة.\n- تحميل ذكي.\n- جودة مقترحة."},
    {"name": "🎵 تحميل الصوت", "type": "url", "content": "https://t.me/ahmbyy123"}
]

STATS_FILE = "stats.json"
def load_stats():
    try:
        with open(STATS_FILE, 'r') as f: return json.load(f)
    except: return {"users": [], "downloads": 0, "daily": {}, "reactions": {"👍": 0, "👎": 0, "❤️": 0}}
def save_stats(s):
    with open(STATS_FILE, 'w') as f: json.dump(s, f)
def record_user(uid):
    s = load_stats()
    if uid not in s.get("users", []):
        s["users"] = s.get("users", []) + [uid]
        save_stats(s)
def record_download():
    s = load_stats()
    s["downloads"] = s.get("downloads", 0) + 1
    today = str(datetime.date.today())
    s["daily"][today] = s["daily"].get(today, 0) + 1
    save_stats(s)
def record_reaction(emoji):
    s = load_stats()
    if "reactions" not in s:
        s["reactions"] = {"👍": 0, "👎": 0, "❤️": 0}
    if emoji in s["reactions"]:
        s["reactions"][emoji] += 1
    save_stats(s)
def get_stats():
    s = load_stats()
    r = s.get("reactions", {"👍": 0, "👎": 0, "❤️": 0})
    return (
        f"👥 المستخدمون: {len(s.get('users', []))}\n"
        f"📥 التحميلات: {s.get('downloads', 0)}\n"
        f"👍 {r.get('👍', 0)} | 👎 {r.get('👎', 0)} | ❤️ {r.get('❤️', 0)}"
    )

BANS_FILE = "bans.json"
def load_bans():
    try:
        with open(BANS_FILE, 'r') as f: return json.load(f)
    except: return []
def save_bans(bans):
    with open(BANS_FILE, 'w') as f: json.dump(bans, f)
def is_banned(uid):
    return uid in load_bans()
def ban_user(uid):
    bans = load_bans()
    if uid not in bans:
        bans.append(uid)
        save_bans(bans)
        return True
    return False
def unban_user(uid):
    bans = load_bans()
    if uid in bans:
        bans.remove(uid)
        save_bans(bans)
        return True
    return False

QUALITY_OPTIONS = {
    "144": "144p",
    "360": "360p",
    "480": "480p",
    "720": "720p",
    "1080": "1080p"
}
DEFAULT_QUALITY = "720"
USER_SETTINGS_FILE = "user_settings.json"
def load_user_settings():
    try:
        with open(USER_SETTINGS_FILE, 'r') as f: return json.load(f)
    except: return {}
def save_user_settings(settings):
    with open(USER_SETTINGS_FILE, 'w') as f: json.dump(settings, f)
def get_user_quality(uid):
    settings = load_user_settings()
    return str(settings.get(str(uid), DEFAULT_QUALITY))
def set_user_quality(uid, quality):
    settings = load_user_settings()
    settings[str(uid)] = quality
    save_user_settings(settings)
def get_format_str(height_str, audio_only=False):
    if audio_only:
        return "bestaudio/best"
    if height_str and height_str.isdigit():
        return f"bestvideo[height<={height_str}]+bestaudio/best[height<={height_str}]"
    return "bestvideo+bestaudio/best"

MAINTENANCE_FILE = "maintenance.json"
def load_maintenance():
    try:
        with open(MAINTENANCE_FILE, 'r') as f: return json.load(f).get("status", False)
    except: return False
def save_maintenance(status):
    with open(MAINTENANCE_FILE, 'w') as f: json.dump({"status": status}, f)

CONFIG_FILE = "bot_config.json"
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f: return json.load(f)
    except: return {"channels": [CHANNEL_ID]}
def save_config(config):
    with open(CONFIG_FILE, 'w') as f: json.dump(config, f, ensure_ascii=False, indent=4)
def get_current_channels():
    config = load_config()
    return config.get("channels", [CHANNEL_ID])
def add_channel(new_channel):
    config = load_config()
    if new_channel not in config.get("channels", []):
        config.setdefault("channels", []).append(new_channel)
        save_config(config)
        return True
    return False
def set_single_channel(new_channel):
    config = load_config()
    config["channels"] = [new_channel]
    save_config(config)
    return True

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def load_buttons():
    try:
        with open('buttons.json', 'r') as f: return json.load(f)
    except: return []
def save_buttons(b):
    with open('buttons.json', 'w') as f: json.dump(b, f)

async def check_sub(uid, ctx):
    channels = get_current_channels()
    for ch in channels:
        try:
            m = await ctx.bot.get_chat_member(ch, uid)
            if m.status in ['member', 'administrator', 'creator']:
                return True
        except:
            continue
    return False

async def start(update: Update, context: CallbackContext):
    if is_banned(update.effective_user.id):
        await update.message.reply_text("⛔ أنت محظور.")
        return
    record_user(update.effective_user.id)
    await update.message.reply_text(
        "🔥 **مرحباً بك في بوت التحميل الذكي!**\n\n"
        "🎯 أرسل رابط فيديو لاختيار الجودة والتحميل.\n\n"
        "⚙️ **الأوامر:**\n"
        "/start - البداية\n"
        "/menu - الأزرار المخصصة\n"
        "/quality - الجودة الافتراضية\n"
        "/search - بحث يوتيوب\n"
        "/gif - تحويل لـ GIF\n"
        "/setchannel - (للأدمن) تغيير قناة الاشتراك\n"
        "/admin - لوحة الأدمن"
    )

async def menu(update: Update, context: CallbackContext):
    if is_banned(update.effective_user.id):
        await update.message.reply_text("⛔ أنت محظور.")
        return
    keyboard = []
    for btn in CUSTOM_BUTTONS:
        if btn['type'] == 'url':
            keyboard.append([InlineKeyboardButton(btn['name'], url=btn['content'])])
        elif btn['type'] == 'message':
            keyboard.append([InlineKeyboardButton(btn['name'], callback_data=f"custom_msg_{CUSTOM_BUTTONS.index(btn)}")])
    for b in load_buttons():
        keyboard.append([InlineKeyboardButton(b['name'], callback_data=f"old_btn_{b['id']}")])
    if keyboard:
        await update.message.reply_text("✨ اختر:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("لا توجد أزرار.")

async def set_channel_cmd(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID: return
    channels = get_current_channels()
    txt = "القنوات الحالية:\n"
    for i, ch in enumerate(channels):
        txt += f"{i+1}. {ch}\n"
    txt += "\nأرسل معرف القناة الجديد (مثال: @MyNewChannel):"
    context.user_data['awaiting_channel'] = True
    await update.message.reply_text(txt)

async def awaiting_channel_id(update: Update, context: CallbackContext):
    new_channel = update.message.text.strip()
    if not new_channel.startswith('@'):
        await update.message.reply_text("❌ يجب أن يبدأ معرف القناة بـ @")
        return
    set_single_channel(new_channel)
    await update.message.reply_text(f"✅ تم تعيين قناة الاشتراك إلى:\n{new_channel}")
    context.user_data.clear()

async def handle_msg(update: Update, context: CallbackContext):
    if is_banned(update.effective_user.id):
        await update.message.reply_text("⛔ أنت محظور.")
        return
    if load_maintenance() and update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🛠️ البوت في وضع الصيانة.")
        return
    user = update.effective_user
    if not await check_sub(user.id, context):
        channels = get_current_channels()
        kb = []
        if channels:
            kb.append([InlineKeyboardButton("اشترك", url=f"https://t.me/{channels[0][1:]}")])
        kb.append([InlineKeyboardButton("تحققت", callback_data="check_sub")])
        await update.message.reply_text("اشترك أولاً:", reply_markup=InlineKeyboardMarkup(kb))
        return
    url = update.message.text
    record_user(user.id)
    kb = []
    row = []
    for qid, qname in QUALITY_OPTIONS.items():
        row.append(InlineKeyboardButton(qname, callback_data=f"dl_quality_{qid}_{quote(url, safe='')}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton("🎵 صوت فقط", callback_data=f"dl_audio_{quote(url, safe='')}")])
    await update.message.reply_text("اختر الجودة:", reply_markup=InlineKeyboardMarkup(kb))

async def quality_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    parts = q.data.split('_', 2)
    height_str = parts[1]
    url = unquote(parts[2])
    msg = q.message
    try:
        with youtube_dl.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            available_heights = set()
            for f in formats:
                if f.get('height'):
                    available_heights.add(f.get('height'))
            if available_heights:
                max_available = max(available_heights)
                requested_height = int(height_str) if height_str.isdigit() else 0
                if requested_height > max_available:
                    best_name = QUALITY_OPTIONS.get(str(max_available), f"{max_available}p")
                    kb = [
                        [InlineKeyboardButton("✅ نعم", callback_data=f"accept_best_{max_available}_{quote(url, safe='')}")],
                        [InlineKeyboardButton("❌ لا", callback_data=f"reject_quality_{quote(url, safe='')}")]
                    ]
                    await msg.edit_text(
                        f"⚠️ الجودة {QUALITY_OPTIONS.get(height_str, height_str)} غير متوفرة.\n"
                        f"هل تريد تحميل أفضل جودة متوفرة ({best_name})؟",
                        reply_markup=InlineKeyboardMarkup(kb)
                    )
                    return
        await do_download(update, context, url, height_str)
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {e}")

async def accept_best_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    parts = q.data.split('_', 3)
    max_quality = parts[2]
    url = unquote(parts[3])
    await q.edit_message_text("⏳ جاري التحميل بأفضل جودة...")
    await do_download(update, context, url, max_quality)

async def reject_quality_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    url = unquote(q.data.split('_', 2)[2])
    kb = []
    row = []
    for qid, qname in QUALITY_OPTIONS.items():
        row.append(InlineKeyboardButton(qname, callback_data=f"dl_quality_{qid}_{quote(url, safe='')}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton("🎵 صوت فقط", callback_data=f"dl_audio_{quote(url, safe='')}")])
    await q.edit_message_text("اختر جودة أخرى:", reply_markup=InlineKeyboardMarkup(kb))

async def do_download(update: Update, context: CallbackContext, url: str, quality: str, audio_only=False):
    msg = update.callback_query.message if update.callback_query else update.message
    reply_to = msg
    status_msg = await msg.reply_text("⏳ جاري التحميل...")
    try:
        format_str = get_format_str(quality, audio_only)
        ydl_opts = {
            'format': format_str,
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if audio_only else []
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            if audio_only:
                fname = fname.rsplit('.', 1)[0] + '.mp3'
            await status_msg.edit_text("⬆️ جاري الرفع...")
            reaction_kb = [[
                InlineKeyboardButton("👍", callback_data=f"react_👍_{quote(url, safe='')}"),
                InlineKeyboardButton("👎", callback_data=f"react_👎_{quote(url, safe='')}"),
                InlineKeyboardButton("❤️", callback_data=f"react_❤️_{quote(url, safe='')}")
            ]]
            if audio_only:
                with open(fname, 'rb') as f:
                    await reply_to.reply_audio(f, title=info.get('title', 'Audio'), reply_markup=InlineKeyboardMarkup(reaction_kb))
            else:
                with open(fname, 'rb') as f:
                    await reply_to.reply_video(f, caption=f"🎬 {info.get('title', 'Video')}", reply_markup=InlineKeyboardMarkup(reaction_kb))
            os.remove(fname)
            await status_msg.delete()
            record_download()
    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ: {e}")

async def audio_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    url = unquote(q.data.split('_', 2)[2])
    await q.edit_message_text("⏳ جاري تحميل الصوت...")
    await do_download(update, context, url, quality=None, audio_only=True)

async def reaction_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    parts = q.data.split('_')
    emoji = parts[1]
    record_reaction(emoji)
    await q.answer(f"شكراً لتفاعلك {emoji}!")

async def quality_cmd(update: Update, context: CallbackContext):
    if is_banned(update.effective_user.id): return
    uid = update.effective_user.id
    current = get_user_quality(uid)
    kb = []
    row = []
    for qid, qname in QUALITY_OPTIONS.items():
        marker = " ✅" if qid == current else ""
        row.append(InlineKeyboardButton(f"{qname}{marker}", callback_data=f"set_quality_{qid}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    await update.message.reply_text("اختر الجودة الافتراضية:", reply_markup=InlineKeyboardMarkup(kb))

async def set_quality_callback(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    quality = q.data.split('_')[2]
    set_user_quality(uid, quality)
    await q.edit_message_text(f"✅ تم تعيين الجودة الافتراضية إلى: {QUALITY_OPTIONS[quality]}")

async def admin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID: return
    maint_status = "✅ مفعل" if load_maintenance() else "❌ معطل"
    kb = [
        [InlineKeyboardButton("➕ زر جديد", callback_data="new_btn")],
        [InlineKeyboardButton("📋 عرض الأزرار", callback_data="list_btns")],
        [InlineKeyboardButton(f"🛠️ وضع الصيانة ({maint_status})", callback_data="toggle_maintenance")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats_callback")],
        [InlineKeyboardButton("🗑️ حذف زر", callback_data="delete_btn_menu")],
        [InlineKeyboardButton("📢 إذاعة جماعية", callback_data="start_broadcast")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user_menu")],
        [InlineKeyboardButton("✅ فك حظر", callback_data="unban_user_menu")]
    ]
    await update.message.reply_text("لوحة التحكم:", reply_markup=InlineKeyboardMarkup(kb))

async def stats_callback(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(get_stats())

async def new_btn(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("أرسل اسم الزر:")
    context.user_data['step'] = 'name'

async def btn_type(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer(); context.user_data['type'] = q.data
    await q.edit_message_text("أرسل المحتوى (رابط أو نص):"); context.user_data['step'] = 'content'

async def check_callback(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer()
    if await check_sub(q.from_user.id, context): await q.edit_message_text("✅ تم التحقق. أرسل الرابط.")
    else: await q.answer("لم تشترك بعد!", show_alert=True)

async def old_btn_click(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer()
    bid = int(q.data.split('_')[2])
    btn = next((b for b in load_buttons() if b['id'] == bid), None)
    if btn:
        if btn['type'] == 'url': await q.edit_message_text(f"🔗 الرابط: {btn['content']}")
        else: await q.edit_message_text(btn['content'])

async def custom_msg_click(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer()
    idx = int(q.data.split('_')[2])
    if idx < len(CUSTOM_BUTTONS): await q.edit_message_text(CUSTOM_BUTTONS[idx]['content'])

async def list_btns_callback(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    btns = load_buttons()
    if not btns:
        await update.callback_query.edit_message_text("لا توجد أزرار.")
        return
    txt = "📋 الأزرار:\n"
    for b in btns:
        txt += f"- {b['name']} (ID: {b['id']})\n"
    await update.callback_query.edit_message_text(txt)

async def delete_btn_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    btns = load_buttons()
    if not btns:
        await update.callback_query.edit_message_text("لا توجد أزرار.")
        return
    kb = [[InlineKeyboardButton(f"{b['name']} (ID: {b['id']})", callback_data=f"confirm_delete_{b['id']}")] for b in btns]
    await update.callback_query.edit_message_text("🗑️ اختر الزر:", reply_markup=InlineKeyboardMarkup(kb))

async def confirm_delete_btn(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer()
    btn_id = int(q.data.split('_')[2])
    btns = load_buttons()
    new_btns = [b for b in btns if b['id'] != btn_id]
    save_buttons(new_btns)
    await q.edit_message_text(f"✅ تم حذف الزر (ID: {btn_id})")

async def toggle_maintenance(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    current = load_maintenance()
    new_status = not current
    save_maintenance(new_status)
    maint_status = "✅ مفعل" if new_status else "❌ معطل"
    await update.callback_query.edit_message_text(f"🛠️ تم تغيير حالة الصيانة إلى: {maint_status}")

async def start_broadcast(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("📢 أرسل الرسالة التي تريد إذاعتها:")
    context.user_data['state'] = BROADCAST_MSG
    return BROADCAST_MSG

async def broadcast_message(update: Update, context: CallbackContext):
    msg = update.message.text
    s = load_stats()
    users = s.get("users", [])
    sent = 0
    failed = 0
    await update.message.reply_text("📡 جاري الإرسال...")
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    await update.message.reply_text(f"✅ اكتملت الإذاعة.\n- عدد المستلمين: {sent}\n- فشل: {failed}")
    context.user_data.clear()
    return ConversationHandler.END

async def ban_user_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🚫 أرسل معرف المستخدم الرقمي (ID) الذي تريد حظره:")
    context.user_data['awaiting_ban'] = True

async def unban_user_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("✅ أرسل معرف المستخدم الرقمي (ID) الذي تريد فك حظره:")
    context.user_data['awaiting_unban'] = True

async def handle_message(update: Update, context: CallbackContext):
    txt = update.message.text
    step = context.user_data.get('step')
    if context.user_data.get('awaiting_channel'):
        await awaiting_channel_id(update, context)
        return
    if context.user_data.get('awaiting_ban'):
        try:
            target_id = int(txt)
            if ban_user(target_id):
                await update.message.reply_text(f"🚫 تم حظر المستخدم: {target_id}")
            else:
                await update.message.reply_text("⚠️ هذا المستخدم محظور بالفعل.")
        except:
            await update.message.reply_text("❌ يرجى إرسال معرف رقمي صحيح.")
        context.user_data.clear()
        return
    if context.user_data.get('awaiting_unban'):
        try:
            target_id = int(txt)
            if unban_user(target_id):
                await update.message.reply_text(f"✅ تم فك حظر المستخدم: {target_id}")
            else:
                await update.message.reply_text("⚠️ هذا المستخدم ليس محظوراً.")
        except:
            await update.message.reply_text("❌ يرجى إرسال معرف رقمي صحيح.")
        context.user_data.clear()
        return
    if step:
        if step == 'name':
            context.user_data['name'] = txt
            kb = [
                [InlineKeyboardButton("رابط", callback_data="type_url"), InlineKeyboardButton("رسالة", callback_data="type_msg")]
            ]
            await update.message.reply_text("اختر النوع:", reply_markup=InlineKeyboardMarkup(kb))
            context.user_data['step'] = 'type'
        elif step == 'content':
            btns = load_buttons()
            btns.append({"id": len(btns)+1, "name": context.user_data['name'], "type": context.user_data['type'], "content": txt})
            save_buttons(btns)
            await update.message.reply_text("✅ تم إنشاء الزر!")
            context.user_data.clear()
        return
    await handle_msg(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("quality", quality_cmd))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("setchannel", set_channel_cmd))
    app.add_handler(CallbackQueryHandler(set_quality_callback, pattern="^set_quality_"))
    app.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats_callback$"))
    app.add_handler(CallbackQueryHandler(reaction_callback, pattern="^react_"))
    app.add_handler(CallbackQueryHandler(new_btn, pattern="^new_btn$"))
    app.add_handler(CallbackQueryHandler(btn_type, pattern="^type_"))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(old_btn_click, pattern="^old_btn_"))
    app.add_handler(CallbackQueryHandler(custom_msg_click, pattern="^custom_msg_"))
    app.add_handler(CallbackQueryHandler(list_btns_callback, pattern="^list_btns$"))
    app.add_handler(CallbackQueryHandler(delete_btn_menu, pattern="^delete_btn_menu$"))
    app.add_handler(CallbackQueryHandler(confirm_delete_btn, pattern="^confirm_delete_"))
    app.add_handler(CallbackQueryHandler(toggle_maintenance, pattern="^toggle_maintenance$"))
    app.add_handler(CallbackQueryHandler(start_broadcast, pattern="^start_broadcast$"))
    app.add_handler(CallbackQueryHandler(ban_user_menu, pattern="^ban_user_menu$"))
    app.add_handler(CallbackQueryHandler(unban_user_menu, pattern="^unban_user_menu$"))
    app.add_handler(CallbackQueryHandler(quality_callback, pattern="^dl_quality_"))
    app.add_handler(CallbackQueryHandler(audio_callback, pattern="^dl_audio_"))
    app.add_handler(CallbackQueryHandler(accept_best_callback, pattern="^accept_best_"))
    app.add_handler(CallbackQueryHandler(reject_quality_callback, pattern="^reject_quality_"))
    conv_broadcast = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast, pattern="^start_broadcast$")],
        states={BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)]},
        fallbacks=[]
    )
    app.add_handler(conv_broadcast)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ البوت المتكامل يعمل!")
    app.run_polling()

if __name__ == "__main__":
    main()