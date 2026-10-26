import os
import sys
import io
import contextlib
import telebot

# --- AYARLAR ---
TOKEN = "8668738139:AAEADWf88umqqg2ohgOdT6J0nBXWVfH9WVo"
bot = telebot.TeleBot(TOKEN)

# Dosyaların geçici olarak kaydedileceği klasör
UPLOAD_FOLDER = "gelen_kodlar"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@bot.message_handler(commands=['start', 'yardim'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "🤖 **Python Dosya Çalıştırıcı Bot'a Hoş Geldin!**\n\n"
        "Bana herhangi bir `.py` uzantılı Python dosyası gönder, kodunu çalıştırıp çıktısını sana anında göndereyim!",
        parse_mode="Markdown"
    )

# Sadece .py uzantılı dosyaları yakalayan handler
@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name

        # Sadece python dosyası mı kontrol et
        if not file_name.endswith('.py'):
            bot.reply_to(message, "❌ Lütfen sadece `.py` uzantılı Python dosyası gönder!")
            return

        # Dosyayı indir ve kaydet
        downloaded_file = bot.download_file(file_info.file_path)
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.reply_to(message, f"📁 `{file_name}` alındı, kod çalıştırılıyor...", parse_mode="Markdown")

        # Kodun çıktısını ve hatalarını yakalamak için hazırlık
        stdout_io = io.StringIO()
        stderr_io = io.StringIO()

        # Dosyadaki kodu oku ve çalıştır
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()

        try:
            with contextlib.redirect_stdout(stdout_io), contextlib.redirect_stderr(stderr_io):
                # Dosya içindeki kodu global alanda çalıştır
                exec(code_content, {})

            output = stdout_io.getvalue()
            error = stderr_io.getvalue()

            result_text = f"📄 **Dosya:** `{file_name}`\n\n"
            if output:
                result_text += f"📤 **Çıktı:**\n```python\n{output}\n```\n"
            if error:
                result_text += f"❌ **Hata (Stderr):**\n```python\n{error}\n```\n"
            if not output and not error:
                result_text += "✅ Kod başarıyla çalıştırıldı (Herhangi bir çıktı üretmedi)."

            bot.reply_to(message, result_text, parse_mode="Markdown")

        except Exception as exec_error:
            bot.reply_to(message, f"❌ **Çalıştırma Hatası:**\n```python\n{exec_error}\n```", parse_mode="Markdown")

        # Geçici dosyayı temizle
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        bot.reply_to(message, f"⚠️ Dosya işlenirken bir hata oluştu: {e}")

if __name__ == '__main__':
    print("🚀 Python Dosya Çalıştırıcı Bot aktif ve dosya bekliyor...")
    bot.infinity_polling()
