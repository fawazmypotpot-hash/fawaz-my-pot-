الاستيراد.logging
استيراد OS.  os
استيراد tempfile. tempfile
 من تحديث استيراد البرقيات telegram   import Update
من telegram.ext استيراد التطبيق، CommandHandler، ContextTypes، MessageHandler، مرشحات telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
استيراد yt_dlp yt_dlp

# إعداد اللوج
logging.basicConfig (basicConfig(
  تنسيق =  "% (asctime) s -% (name) s -% (levelname) s -% (رسالة) s" (s) ، "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  المستوى = تسجيل الدخول.  معلومات. INFO
)

# قراءة التوكن من متغير البيئة (آمن)
توكين ="8687541181:AAH3ep_dhi6-3jD36v7dqylanJ7YOWWMHY""8687541181:AAH3ep_dhi6-3jD36v7dqyylanJ7YOWWmHY"
# استقبال روابط يوتيوب وتنزيل الفيديو
async def handle_youtube (تحديث: تحديث، السياق: ContextTypes.  Default_type): def handle_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
 url = update.message.text.strip () message.text.strip()

     # التحقق أن الرابط من يوتيوب فقط # التحقق أن الرابط من يوتيوب فقط
  إذا لم يكن  "youtube.com"  في URL و  في URL و "youtu.be" ليس في url: "youtube.com" في URL و "youtu.be" ليس في url: if "youtube.com" not in url and "youtu.be" not in url:
          await update.message.reply_text("❌ هذا الكود خاص بروابط يوتيوب فقط.") await update.message.reply_text("❌ هذا الكود خاص بروابط يوتيوب فقط.") 
  العودة. return

  العودة.  

      # استخدام مجلد مؤقت لتجنب تلويث الملفات  
    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
              "format": "best[height<=480]/best",  # جودة 480p لضمان الحجم أقل من 50 ميجا "format": "best[height<=480]/best",  # جودة 480p لضمان الحجم أقل من 50 ميجا 
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "restrictfilenames": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            # إرسال الفيديو
            with open(file_path, "rb") as f:
                await update.message.reply_document(f)

            await update.message.reply_text("✅ تم الإرسال بنجاح!")

            # الملف سيُحذف تلقائياً عند انتهاء كتلة with

        except Exception as e:
            await update.message.reply_text(f"❌ خطأ أثناء التحميل: {e}")

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أرسل رابط فيديو من يوتيوب وسأقوم بتنزيله لك مباشرة.")

# تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube))
    app.run_polling()

if __name__ == "__main__":
    main()
