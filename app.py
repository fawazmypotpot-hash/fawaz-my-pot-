الاستيراد.تسجيل  الدخول.
الاستيراد. OS.  . os.
منمنتحديث
من...Telegram.ext    الاستيراد.   التطبيق،.
الاستيراد.

# إعداد اللوج
تسجيل.التكسير  الأساسي.  (basicConfig(
 الشكل = "% (asctime) s -% (name) s -% (levelname) s -% (رسالة) s" (s) ، "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  المستوى   المستوى = تسجيل الدخول.     معلومات.
)

رمز = "8687541181: AGImfmybwuBWOoH6BtxSVtSOD8zfquQ4-A""8687541181: AGImfmybwuBWOoH6BtxSVtSOD8zfquQ4-A"

# استقبال روابط يوتيوب وتنزيل الفيديو
ASYNC.ديف. مقبض_يوتيوب. (تحديث: تحديث، السياق: ContextTypes.  :  تحديث،  السياق: ContextTypes.   Default_type): def handle_youtube(تحديث: تحديث، السياق: ContextTypes.DEFAULT_TYPE):
 URL = تحديث. رسالة..text.strip () message.النص...شريط.()

     # التحقق أن الرابط من يوتيوب فقط  
      إذا لم يكن      "youtube.com"   إذا...شريط.في URL و  في URL و   إذا...شريط.في URL و  في URL و     
          await update.message.reply_text("❌ هذا الكود خاص بروابط يوتيوب فقط.")  
   العودة.  return 

   العودة.   

    ydl_opts = {
          "format": "best[height<=720]/best",  # جودة متوسطة لتقليل الحجم  
        "outtmpl": "%(title)s.%(ext)s"
 } }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
 } 
 "outtmpl": "% (العنوان) s.% (ext) s" 

         # تنظيف الاسم من الرموز غير المدعومة 
        safe_path = file_path.replace("·", "_").replace(":", "_").replace("|", "_").strip()
        if file_path != safe_path:
            os.rename(file_path, safe_path)
            file_path = safe_path

        # إرسال الفيديو
        await update.message.reply_document(open(file_path, "rb"))
        await update.message.reply_text("✅ تم الإرسال بنجاح، جاري تنظيف السيرفر...")

        # حذف الفيديو بعد الإرسال
        if os.path.exists(file_path):
            os.remove(file_path)

        # حذف الملفات المؤقتة
        for ext in [".mp4", ".webm", ".mkv"]:
            for f in os.listdir():
                if f.endswith(ext):
                    os.remove(f)

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
