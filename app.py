import logging
import os
من... telegram import Update
من... telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import yt_dlp

# إعداد اللوج
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ضع توكن البوت هنا
TOKEN = "8687541181:AAH3ep_dhi6-3jD36v7dqyylanJ7YOWWmHY"

# استقبال روابط يوتيوب وتنزيل الفيديو
asyncdef handle_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # التحقق أن الرابط من يوتيوب فقط
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ هذا الكود خاص بروابط يوتيوب فقط.")
        return

    await update.message.reply_text("⏳ جاري التحميل من يوتيوب...")

    ydl_opts = {
        "format": "best[height<=720]/best",  # جودة متوسطة لتقليل الحجم
        "outtmpl": "%(title)s.%(ext)s"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        # تنظيف الاسم من الرموز غير المدعومة
        safe_path = file_path.replace("·", "_").replace(":", "_").replace("|", "_").strip()
        if file_path != safe_path:
            os.rename(file_path, safe_path)
            file_path = safe_path

        # إرسال الفيديو# إرسال الفيديو # إرسال الفيديو
 في انتظار update.message.reply_document (مفتوح (file_path، "rb")) message.reply_document (مفتوح (file_path، "rb")) await update.message.reply_document(open(File_Path، "rb"))
         أنتظر! update.await update.message.reply_text("✅ تم الإرسال بنجاح، جاري تنظيف السيرفر...") message.reply_text("✅ تم الإرسال بنجاح، جاري تنظيف السيرفر...") await update.message.reply_text("✅ تم الإرسال بنجاح، جاري تنظيف السيرفر...")

        # حذف الفيديو بعد الإرسال# حذف الفيديو بعد الإرسال # حذف الفيديو بعد الإرسال
 إذا os.path.exists (file_path): path.exists (file_path): if os.path.exists(file_path):
 os.remove (file_path) remove(file_path)

        # حذف الملفات المؤقتة# حذف الملفات المؤقتة # حذف الملفات المؤقتة
 للنص في ["..mp4 "، ".webm"، ".mkv"]: ["..mp4 "، ".webm"، ".mkv"]: for ext in [".mp4", ".webm", ".mkv"]:
            for f in os.listdir():
 ل f في os.listdir (): 
                    os.remove(f)

    except Exception as e:
          await update.message.reply_text(f"❌ خطأ أثناء التحميل: {e}") await update.message.reply_text(f"❌ خطأ أثناء التحميل: {e}") 

# أمر /start
# أمر /start
      await update.message.reply_text("👋 أرسل رابط فيديو من يوتيوب وسأقوم بتنزيله لك مباشرة.") await update.message.reply_text("👋 أرسل رابط فيديو من يوتيوب وسأقوم بتنزيله لك مباشرة.") 

# تشغيل البوت
# تشغيل البوت
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube))
    app.run_polling()

if __name__ == "__main__":
    main((
