import os
import subprocess
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8937463436:AAHpigAH5KKlSNyZIQjPThZWSksbdeEZ3oY"
ADMIN_CHAT_ID = "8770418133"
ADMIN_USERNAME = "lanetliymis"
KANAL_USERNAME = "@lanetrbot"  # Kanal kullanıcı adı
KANAL_LINKI = "https://t.me/lanetrbot"

bot = telebot.TeleBot(TOKEN)

BEKLEYENLER_KLASORU = "onay_bekleyenler"
AKTIF_BOTLAR = "aktif_botlar"

os.makedirs(BEKLEYENLER_KLASORU, exist_ok=True)
os.makedirs(AKTIF_BOTLAR, exist_ok=True)

dosya_sahipleri = {}
kullanici_bot_sayisi = {}
premium_kullanicilar = set()

# Kullanıcının kanala üye olup olmadığını kontrol eden fonksiyon
def kanala_uye_mi(user_id):
    if str(user_id) == ADMIN_CHAT_ID:
        return True
    try:
        durum = bot.get_chat_member(KANAL_USERNAME, user_id).status
        if durum in ['creator', 'administrator', 'member']:
            return True
    except Exception as e:
        print(f"Kanal kontrol hatası: {e}")
    return False

def kanal_zorunluluk_mesaji(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Kanala Katıl", url=KANAL_LINKI))
    markup.add(InlineKeyboardButton("🔄 Katıldım, Kontrol Et", callback_data="kontrol_et"))
    
    bot.send_message(
        chat_id, 
        f"❌ Botu kullanabilmek ve dosya yükleyebilmek için öncelikle resmi kanalımıza katılman gerekiyor!\n\n"
        f"👉 Kanal: {KANAL_USERNAME}\n\n"
        f"Katıldıktan sonra aşağıdaki **'Katıldım, Kontrol Et'** butonuna basabilirsin.",
        reply_markup=markup
    )

def ana_menu_klavyesi(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_proje_gonder = KeyboardButton("📂 Python Dosyası Gönder")
    btn_durum = KeyboardButton("📊 Botlarımın Durumu")
    btn_yardim = KeyboardButton("🛠 Yardım")
    
    markup.add(btn_proje_gonder, btn_durum, btn_yardim)
    
    if str(user_id) == ADMIN_CHAT_ID:
        btn_admin = KeyboardButton("👑 Admin Paneli")
        markup.add(btn_admin)
        
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    
    if not kanala_uye_mi(user_id):
        kanal_zorunluluk_mesaji(user_id)
        return

    hosgeldin_mesaji = (
        "⚡ **Python Bot Yönetim Sistemi** 📂\n\n"
        "🔥 Python dosyanı gönder, onaylandığında 7/24 çalıştıralım.\n\n"
        "⚠️ **Kurallar:**\n"
        "• Normal Üyeler: En fazla **1** bot yükleyebilir.\n"
        "• Premium Üyeler: En fazla **3** bot yükleyebilir."
    )
    bot.send_message(user_id, hosgeldin_mesaji, reply_markup=ana_menu_klavyesi(user_id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "kontrol_et")
def kontrol_et_callback(call):
    user_id = call.message.chat.id
    if kanala_uye_mi(user_id):
        bot.answer_callback_query(call.id, "✅ Kanala katılımınız onaylandı!")
        try:
            bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        except:
            pass
        
        hosgeldin_mesaji = (
            "🎉 Harika! Kanala katıldığın doğrulandı.\n\n"
            "⚡ **Python Bot Yönetim Sistemi** aktif edilmiştir."
        )
        bot.send_message(user_id, hosgeldin_mesaji, reply_markup=ana_menu_klavyesi(user_id), parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "❌ Henüz kanala katıldığını tespit edemedim! Lütfen önce katıl.", show_alert=True)

@bot.message_handler(func=lambda message: message.text == "📂 Python Dosyası Gönder")
def proje_gonder_bilgi(message):
    user_id = message.chat.id
    if not kanala_uye_mi(user_id):
        kanal_zorunluluk_mesaji(user_id)
        return

    mevcut_botlar = kullanici_bot_sayisi.get(user_id, [])
    is_premium = user_id in premium_kullanicilar or str(user_id) == ADMIN_CHAT_ID
    
    if not is_premium and len(mevcut_botlar) >= 1:
        bot.reply_to(
            message, 
            f"❌ Zaten 1 aktif botun var! Birden fazla atamazsın, çünkü **premium** alman lazım.\n"
            f"💎 Premium almak için admin hesabına yaz: @{ADMIN_USERNAME}", 
            reply_markup=ana_menu_klavyesi(user_id), 
            parse_mode="Markdown"
        )
        return
        
    if is_premium and len(mevcut_botlar) >= 3 and str(user_id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "❌ Premium hesaplar için maksimum bot sınırına (3 adet) ulaştın!", reply_markup=ana_menu_klavyesi(user_id))
        return

    bot.reply_to(message, "Lütfen göndermek istediğin `.py` dosyasını **belge (document)** olarak sohbete yükle. 📂", reply_markup=ana_menu_klavyesi(user_id))

@bot.message_handler(func=lambda message: message.text == "📊 Botlarımın Durumu")
def bot_durumu(message):
    user_id = message.chat.id
    if not kanala_uye_mi(user_id):
        kanal_zorunluluk_mesaji(user_id)
        return

    mevcut_botlar = kullanici_bot_sayisi.get(user_id, [])
    
    if mevcut_botlar:
        liste = "\n".join([f"• `{b}`" for b in mevcut_botlar])
        bot.reply_to(message, f"🟢 **Aktif Botların:**\n{liste}", reply_markup=ana_menu_klavyesi(user_id), parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚪ Sistemde çalışan aktif bir botun bulunmuyor.", reply_markup=ana_menu_klavyesi(user_id))

@bot.message_handler(func=lambda message: message.text == "🛠 Yardım")
def yardim_bilgi(message):
    bot.reply_to(message, f"Sorularınız ve Premium üyelik için: @{ADMIN_USERNAME}", reply_markup=ana_menu_klavyesi(message.chat.id))

# --- ADMİN PANELİ ---
@bot.message_handler(func=lambda message: message.text == "👑 Admin Paneli")
def admin_paneli(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("➕ Kullanıcıyı Premium Yap", callback_data="admin_premium_ekle"),
        InlineKeyboardButton("📋 Premium Listesini Gör", callback_data="admin_premium_liste"),
        InlineKeyboardButton("🗑 Aktif Botları Yönet / Sil", callback_data="admin_botlari_listele")
    )
    bot.send_message(message.chat.id, "👑 **Admin Kontrol Paneli**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_") or call.data.startswith("silbot_"))
def admin_callbacks(call):
    if str(call.from_user.id) != ADMIN_CHAT_ID:
        bot.answer_callback_query(call.id, "Yetkin yok!")
        return

    data = call.data

    if data == "admin_premium_ekle":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "✏️ Premium yapılacak kullanıcının **Telegram ID**'sini yaz:")
        bot.register_next_step_handler(msg, premium_ekleme_islem)

    elif data == "admin_premium_liste":
        bot.answer_callback_query(call.id)
        if not premium_kullanicilar:
            bot.send_message(call.message.chat.id, "📋 Henüz kayıtlı premium kullanıcı yok.")
        else:
            liste = "\n".join([f"• `{uid}`" for uid in premium_kullanicilar])
            bot.send_message(call.message.chat.id, f"📋 **Premium Kullanıcılar (Max 3 Bot):**\n{liste}", parse_mode="Markdown")

    elif data == "admin_botlari_listele":
        bot.answer_callback_query(call.id)
        aktif_dosyalar = os.listdir(AKTIF_BOTLAR)
        if not aktif_dosyalar:
            bot.send_message(call.message.chat.id, "⚪ `aktif_botlar` klasöründe hiç dosya yok.")
        else:
            markup = InlineKeyboardMarkup(row_width=1)
            for dosya in aktif_dosyalar:
                markup.add(InlineKeyboardButton(f"🗑 Sil: {dosya}", callback_data=f"silbot_{dosya}"))
            bot.send_message(call.message.chat.id, "🗑 **Silmek istediğin botu seç:**", reply_markup=markup, parse_mode="Markdown")

    elif data.startswith("silbot_"):
        dosya_adi = data.replace("silbot_", "")
        dosya_yolu = os.path.join(AKTIF_BOTLAR, dosya_adi)
        
        if os.path.exists(dosya_yolu):
            os.remove(dosya_yolu)
            
            for uid, botlar in kullanici_bot_sayisi.items():
                if dosya_adi in botlar:
                    botlar.remove(dosya_adi)
                    try:
                        # BURASI DÜZELTİLDİ ({dosya_adi} -> süslü parantez kapatıldı)
                        bot.send_message(uid, f"⚠️ Yönetici tarafından `{dosya_adi}` adlı botun sistemden silindi.")
                    except:
                        pass
                    break
            
            bot.answer_callback_query(call.id, f"✅ {dosya_adi} silindi!")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🗑 Başarıyla silindi: `{dosya_adi}`",
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "❌ Dosya zaten bulunamadı!")

def premium_ekleme_islem(message):
    try:
        yeni_premium_id = int(message.text.strip())
        premium_kullanicilar.add(yeni_premium_id)
        bot.reply_to(message, f"✅ `{yeni_premium_id}` ID'li kullanıcı **Premium** yapıldı (Artık 3 bot hakkı var).", parse_mode="Markdown")
        bot.send_message(yeni_premium_id, "🎉 Tebrikler! Hesabın **Premium** statüsüne yükseltildi. Artık en fazla 3 bot çalıştırabilirsin.")
    except ValueError:
        bot.reply_to(message, "❌ Geçersiz ID! Sadece rakam gir.")

# --- DOSYA ALMA VE KONTROL ---
@bot.message_handler(content_types=['document'])
def dosya_al(message):
    try:
        user_id = message.chat.id
        if not kanala_uye_mi(user_id):
            kanal_zorunluluk_mesaji(user_id)
            return

        doc = message.document
        dosya_adi = doc.file_name
        dosya_boyutu = doc.file_size

        if not dosya_adi or not dosya_adi.endswith('.py'):
            bot.reply_to(message, "❌ Sadece .py uzantılı Python dosyaları kabul edilir!", reply_markup=ana_menu_klavyesi(user_id))
            return

        mevcut_botlar = kullanici_bot_sayisi.get(user_id, [])
        is_premium = user_id in premium_kullanicilar or str(user_id) == ADMIN_CHAT_ID

        if not is_premium and len(mevcut_botlar) >= 1:
            bot.reply_to(
                message, 
                f"❌ Zaten 1 aktif botun var! Birden fazla atamazsın, çünkü **premium** alman lazım.\n"
                f"💎 Premium almak için admin hesabına yaz: @{ADMIN_USERNAME}", 
                reply_markup=ana_menu_klavyesi(user_id), 
                parse_mode="Markdown"
            )
            return

        if is_premium and len(mevcut_botlar) >= 3 and str(user_id) != ADMIN_CHAT_ID:
            bot.reply_to(message, "❌ Premium hesaplar en fazla 3 bot yükleyebilir!", reply_markup=ana_menu_klavyesi(user_id))
            return

        if dosya_boyutu > (25 * 1024 * 1024):
            bot.reply_to(message, "❌ Dosya boyutu 25 MB'dan büyük olamaz!", reply_markup=ana_menu_klavyesi(user_id))
            return

        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        dosya_yolu = os.path.join(BEKLEYENLER_KLASORU, dosya_adi)
        with open(dosya_yolu, 'wb') as f:
            f.write(downloaded_file)
            
        dosya_sahipleri[dosya_adi] = user_id
        gonderen = message.from_user.username or message.from_user.first_name
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✅ Onayla ve Çalıştır", callback_data=f"onayla_{dosya_adi}"),
            InlineKeyboardButton("❌ Reddet", callback_data=f"reddet_{dosya_adi}")
        )
        
        with open(dosya_yolu, 'rb') as f:
            caption = (
                f"📥 **Yeni Python Dosyası İnceleme Talebi!**\n"
                f"👤 Gönderen: @{gonderen} (ID: {user_id})\n"
                f"📄 Dosya: `{dosya_adi}`"
            )
            bot.send_document(ADMIN_CHAT_ID, f, caption=caption, reply_markup=markup, parse_mode="Markdown")
            
        bot.reply_to(message, "✅ Python dosyan yöneticiye iletildi.", reply_markup=ana_menu_klavyesi(user_id))
        
    except Exception as e:
        print(f"HATA: {e}")
        bot.reply_to(message, "❌ Dosya işlenirken hata oluştu.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("onayla_") or call.data.startswith("reddet_"))
def callback_query(call):
    if str(call.from_user.id) != ADMIN_CHAT_ID:
        bot.answer_callback_query(call.id, "Yetkin yok!")
        return

    data = call.data
    
    if data.startswith("onayla_"):
        dosya_adi = data.replace("onayla_", "")
        kaynak = os.path.join(BEKLEYENLER_KLASORU, dosya_adi)
        
        if os.path.exists(kaynak):
            hedef_yol = os.path.join(AKTIF_BOTLAR, dosya_adi)
            os.rename(kaynak, hedef_yol)

            subprocess.Popen(["python3", hedef_yol])
            
            bot.answer_callback_query(call.id, f"{dosya_adi} onaylandı!")
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=f"✅ **ONAYLANDI VE ÇALIŞTIRILDI**\n📄 Dosya: `{dosya_adi}`",
                parse_mode="Markdown"
            )
            
            if dosya_adi in dosya_sahipleri:
                user_id = dosya_sahipleri[dosya_adi]
                if user_id not in kullanici_bot_sayisi:
                    kullanici_bot_sayisi[user_id] = []
                kullanici_bot_sayisi[user_id].append(dosya_adi)
                
                bot.send_message(user_id, f"🎉 Tebrikler! `{dosya_adi}` adlı dosyan onaylandı ve çalıştırıldı!", parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "Dosya bulunamadı!")

    elif data.startswith("reddet_"):
        dosya_adi = data.replace("reddet_", "")
        kaynak = os.path.join(BEKLEYENLER_KLASORU, dosya_adi)
        
        if os.path.exists(kaynak):
            os.remove(kaynak)
            
        bot.answer_callback_query(call.id, f"{dosya_adi} reddedildi.")
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"❌ **REDDEDİLDİ**\n📄 Dosya: `{dosya_adi}`",
            parse_mode="Markdown"
        )
        
        if dosya_adi in dosya_sahipleri:
            user_id = dosya_sahipleri[dosya_adi]
            bot.send_message(user_id, f"❌ Üzgünüz, `{dosya_adi}` adlı dosyan reddedildi.", parse_mode="Markdown")

if __name__ == "__main__":
    print("Lanet Robot Botu kanal zorunluluğu ile aktif ve çalışıyor...")
    bot.infinity_polling()
        
