import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters
import yt_dlp

TOKEN = "8937463436:AAET4lPQv6u9Smph3T5mcct4oimalRw4Xxw"
DEV_TAG = "@lanetliymis"
VERSION = "1.0"

# Ana menü klavyesi
def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📍 YouTube", callback_data="menu_youtube")],
        [InlineKeyboardButton("🕉️ Instagram", callback_data="menu_instagram")],
        [InlineKeyboardButton("💣 Tiktok", callback_data="menu_tiktok")]
    ])

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Hoş Geldin!**\n\n"
        "Lütfen indirmek istediğin platformu aşağıdaki butonlardan seç:"
    )
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        context.user_data['download_mode'] = None
        # Mesajı günceller (yeni mesaj atmaz)
        await query.message.edit_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    else:
        # /start ilk kez yazıldığında mesajı kaydet
        msg = await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
        context.user_data['bot_msg_id'] = msg.message_id
        context.user_data['chat_id'] = update.effective_chat.id

# Buton tıklamaları (Mesajı güncelleyerek ilerler)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "menu_youtube":
        context.user_data['download_mode'] = 'youtube'
        text = "📍 **YouTube İndirici Seçildi**\n\nŞimdi bana bir YouTube video linki gönder."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]])
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        
    elif query.data == "menu_instagram":
        context.user_data['download_mode'] = 'instagram'
        text = "🕉️ **Instagram İndirici Seçildi**\n\nŞimdi bana bir Instagram linki gönder."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]])
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        
    elif query.data == "menu_tiktok":
        context.user_data['download_mode'] = 'tiktok'
        text = "💣 **Tiktok İndirici Seçildi**\n\nŞimdi bana bir Tiktok linki gönder."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]])
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        
    elif query.data == "main_menu":
        context.user_data['download_mode'] = None
        text = "👋 **Hoş Geldin!**\n\nLütfen indirmek istediğin platformu aşağıdaki butonlardan seç:"
        await query.message.edit_text(text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

# Gelen linkleri işleme ve tek mesajı güncelleme sistemi
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Kullanıcının gönderdiği link mesajını anında siliyoruz ki sohbet kirletmesin
    try:
        await update.message.delete()
    except Exception:
        pass

    chat_id = update.effective_chat.id
    bot_msg_id = context.user_data.get('bot_msg_id')
    current_mode = context.user_data.get('download_mode')
    url = update.message.text
    
    # Eğer botun güncelleyeceği aktif bir mesaj ID'si yoksa (örn: direkt link atıldıysa)
    if not bot_msg_id:
        new_msg = await context.bot.send_message(chat_id=chat_id, text="⚙️ Sistem başlatılıyor...")
        bot_msg_id = new_msg.message_id
        context.user_data['bot_msg_id'] = bot_msg_id

    # Mod seçilmemişse
    if not current_mode:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=bot_msg_id,
            text="⚠️ **Önce menüden hangi platformdan video indireceğini seçmelisin!**",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Platform doğrulama
    is_valid = False
    error_message = ""

    if current_mode == 'youtube':
        if "youtube.com" in url or "youtu.be" in url:
            is_valid = True
        else:
            error_message = "Seçtiğiniz menü YouTube menüsüdür! Lütfen geçerli bir YouTube linki gönderin."
            
    elif current_mode == 'instagram':
        if "instagram.com" in url:
            is_valid = True
        else:
            error_message = "Seçtiğiniz menü Instagram menüsüdür! Lütfen geçerli bir Instagram linki gönderin."
            
    elif current_mode == 'tiktok':
        if "tiktok.com" in url or "vm.tiktok.com" in url:
            is_valid = True
        else:
            error_message = "Seçtiğiniz menü Tiktok menüsüdür! Lütfen geçerli bir Tiktok linki gönderin."

    # Yanlış platform linki girildiyse
    if not is_valid:
        error_text = (
            "📄 Sonuçlar — Olumsuz\n\n"
            "🔴 Video Yüklenmedi\n"
            "├─ DURUM: Olumsuz\n"
            f"├─ MESAJ: {error_message}\n"
            f"├─ DEVELOPER: {DEV_TAG}\n"
            f"├─ VERSION: {VERSION}\n"
            "└─ Kapat / Ana Menü"
        )
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=bot_msg_id,
            text=error_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Kapat / Ana Menü", callback_data="main_menu")]])
        )
        return

    # İndirme aşaması mesajı güncelleme
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=bot_msg_id,
        text="📥 **Video indiriliyor, lütfen bekle...**",
        parse_mode="Markdown"
    )

    output_template = '%(id)s.%(ext)s'
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_template,
        'max_filesize': 50 * 1024 * 1024,
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Videoyu gönder
        with open(filename, 'rb') as video_file:
            await context.bot.send_video(chat_id=chat_id, video=video_file)

        # Başarılı sonuç raporu ile mesajı güncelle
        success_text = (
            "📄 Sonuçlar — Olumlu\n\n"
            "🟢 Video Yüklendi\n"
            "├─ DURUM: Olumlu\n"
            "├─ MESAJ: Video Yüklendi\n"
            f"├─ DEVELOPER: {DEV_TAG}\n"
            f"├─ VERSION: {VERSION}\n"
            "└─ Kapat / Ana Menü"
        )
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=bot_msg_id,
            text=success_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Kapat / Ana Menü", callback_data="main_menu")]])
        )

        if filename and os.path.exists(filename):
            os.remove(filename)
            
        context.user_data['download_mode'] = None

    except Exception as e:
        # Hatalı sonuç raporu ile mesajı güncelle
        error_text = (
            "📄 Sonuçlar — Olumsuz\n\n"
            "🔴 Video Yüklenmedi\n"
            "├─ DURUM: Olumsuz\n"
            "├─ MESAJ: Video Yüklenemedi\n"
            f"├─ DEVELOPER: {DEV_TAG}\n"
            f"├─ VERSION: {VERSION}\n"
            "└─ Kapat / Ana Menü"
        )
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=bot_msg_id,
            text=error_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Kapat / Ana Menü", callback_data="main_menu")]])
        )

        if filename and os.path.exists(filename):
            os.remove(filename)
            
        context.user_data['download_mode'] = None

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot çalışıyor...")
    app.run_polling()
