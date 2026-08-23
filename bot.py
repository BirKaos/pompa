import telebot
from telebot import types
import requests
import json
import re
from urllib.parse import quote
import io

TOKEN = "8685751277:AAFiz53DXjlHrI6Ay2oUZnfW8ZdDpPnrrQo"
KANAL_ID = "@lanetrbot"
ADMIN_ID = 8770418133

bot = telebot.TeleBot(TOKEN)
kullanici_verileri = {}
engellenenler = set()

def kullanici_kanalda_mi(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        uye = bot.get_chat_member(KANAL_ID, user_id)
        durum = uye.status
        if durum in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception as e:
        print(f"Kanal kontrol hatası ({user_id}): {e}")
        return False

def kanal_kontrol_mesaji(chat_id, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    kanal_buton = types.InlineKeyboardButton("📢 Kanal", url="https://t.me/lanetrbot")
    kontrol_buton = types.InlineKeyboardButton("✅ Katıldım", callback_data="kontrol_et")
    markup.add(kanal_buton, kontrol_buton)
    
    text = "SORGULARI KULLANABİLMENİZ İÇİN AŞAĞIDAKİ KANALLARA KATILMANIZ LAZIM"
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
            return
        except:
            pass
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_paneli(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Bu komutu kullanmaya yetkiniz yok.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚫 Kullanıcı Engelle", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ Engel Kaldır", callback_data="admin_unban"),
        types.InlineKeyboardButton("📊 Engellenenler Listesi", callback_data="admin_list"),
        types.InlineKeyboardButton("❌ Paneli Kapat", callback_data="iptal")
    )
    bot.send_message(message.chat.id, "👑 **Admin Paneline Hoş Geldiniz**\n\nLütfen bir işlem seçin:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_islem(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Yetkiniz yok!", show_alert=True)
        return
    
    action = call.data.split("_")[1]
    chat_id = call.message.chat.id
    
    if action == "ban":
        msg = bot.send_message(chat_id, "✏️ Engellemek istediğiniz kullanıcının **ID** numarasını veya **@kullaniciadi**nı yazın:")
        bot.register_next_step_handler(msg, ban_uygula)
    elif action == "unban":
        msg = bot.send_message(chat_id, "✏️ Engelini kaldırmak istediğiniz kullanıcının **ID** numarasını veya **@kullaniciadi**nı yazın:")
        bot.register_next_step_handler(msg, unban_uygula)
    elif action == "list":
        if not engellenenler:
            bot.answer_callback_query(call.id, "Engellenen kimse yok.", show_alert=True)
        else:
            txt = "🚫 **Engellenen Kullanıcılar:**\n" + "\n".join([f"• `{uid}`" for uid in engellenenler])
            bot.send_message(chat_id, txt, parse_mode="Markdown")

def hedef_id_bul(girdi):
    girdi = girdi.strip()
    if girdi.startswith("@"):
        try:
            chat_info = bot.get_chat(girdi)
            return chat_info.id
        except:
            return None
    else:
        try:
            return int(girdi)
        except:
            return None

def ban_uygula(message):
    if message.from_user.id != ADMIN_ID: return
    uid = hedef_id_bul(message.text)
    if uid:
        engellenenler.add(uid)
        bot.reply_to(message, f"✅ `{uid}` ID'li kullanıcı başarıyla engellendi.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Geçersiz kullanıcı veya ID.")

def unban_uygula(message):
    if message.from_user.id != ADMIN_ID: return
    uid = hedef_id_bul(message.text)
    if uid:
        if uid in engellenenler:
            engellenenler.remove(uid)
            bot.reply_to(message, f"✅ `{uid}` ID'li kullanıcının engeli kaldırıldı.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ Bu kullanıcı zaten engelli değil.")
    else:
        bot.reply_to(message, "❌ Geçersiz kullanıcı veya ID.")

@bot.message_handler(commands=['start'])
def send_start(message):
    user_id = message.from_user.id
    if user_id in engellenenler:
        bot.reply_to(message, "❌ Botu kullanmanız engellenmiştir.")
        return
        
    if not kullanici_kanalda_mi(user_id):
        kanal_kontrol_mesaji(message.chat.id)
        return
    
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
        
    sent = bot.send_message(message.chat.id, "✨ Lütfen bir işlem seçin:")
    kullanici_verileri[user_id] = {"aktif_mesaj_id": sent.message_id}
    ana_menu_gonder(message.chat.id, sent.message_id, sayfa=1)

def ana_menu_gonder(chat_id, message_id, sayfa=1):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    sayfa_1_butonlar = [
        types.InlineKeyboardButton("🔍 TC SORGU", callback_data="menu_tc"),
        types.InlineKeyboardButton("⭐ TC PRO", callback_data="menu_tcpro"),
        types.InlineKeyboardButton("📝 AD SOYAD", callback_data="menu_adsoyad"),
        types.InlineKeyboardButton("⭐ AD SOYAD PRO", callback_data="menu_adsoyadpro"),
        types.InlineKeyboardButton("👨‍👩‍👧‍👦 AİLE", callback_data="menu_aile"),
        types.InlineKeyboardButton("⭐ AİLE PRO", callback_data="menu_ailepro"),
        types.InlineKeyboardButton("🌳 SÜLALE", callback_data="menu_sulale"),
        types.InlineKeyboardButton("⭐ SÜLALE PRO", callback_data="menu_sulalepro"),
        types.InlineKeyboardButton("👶 ÇOCUK", callback_data="menu_cocuk"),
        types.InlineKeyboardButton("💍 EŞ", callback_data="menu_es"),
        types.InlineKeyboardButton("👫 KARDEŞ", callback_data="menu_kardes"),
        types.InlineKeyboardButton("📅 DOĞUM İL/İLÇE", callback_data="menu_dogumtililce"),
        types.InlineKeyboardButton("📋 SOYAD & DOĞUM", callback_data="menu_soyaddogumt"),
        types.InlineKeyboardButton("🏠 ADRES", callback_data="menu_adres"),
        types.InlineKeyboardButton("🏢 İŞ YERİ", callback_data="menu_isyeri"),
        types.InlineKeyboardButton("📜 TAPU", callback_data="menu_tapu")
    ]
    
    sayfa_2_butonlar = [
        types.InlineKeyboardButton("💳 IBAN", callback_data="menu_iban"),
        types.InlineKeyboardButton("📞 GSM'DEN TC", callback_data="menu_gsmtc"),
        types.InlineKeyboardButton("📱 TC'DEN GSM", callback_data="menu_tcgsm"),
        types.InlineKeyboardButton("📶 OPERATÖR", callback_data="menu_gncloperator"),
        types.InlineKeyboardButton("🖼️ VESİKA", callback_data="menu_vesika"),
        types.InlineKeyboardButton("💉 AŞI", callback_data="menu_asi"),
        types.InlineKeyboardButton("🚗 PLAKA", callback_data="menu_plaka"),
        types.InlineKeyboardButton("⚽ BAHİS", callback_data="menu_bahis"),
        types.InlineKeyboardButton("🌐 IP BİLGİ", callback_data="menu_ipinfo"),
        types.InlineKeyboardButton("💊 ECZANE", callback_data="menu_eczane"),
        types.InlineKeyboardButton("🤖 DC TOKEN", callback_data="menu_dcbottoken"),
        types.InlineKeyboardButton("🤖 TG TOKEN", callback_data="menu_tgtoken"),
        types.InlineKeyboardButton("🏥 SGK", callback_data="menu_sgk"),
        types.InlineKeyboardButton("📚 E-OKUL", callback_data="menu_eokul"),
        types.InlineKeyboardButton("🗳️ SEÇMEN", callback_data="menu_secmen"),
        types.InlineKeyboardButton("🅿️ PAPARA", callback_data="menu_papara"),
        types.InlineKeyboardButton("🎓 ÜNİV (TC)", callback_data="menu_universite_tc"),
        types.InlineKeyboardButton("🎓 ÜNİV (AD)", callback_data="menu_universite_ara"),
        types.InlineKeyboardButton("📉 İNİAL (GSM)", callback_data="menu_inial_gsm"),
        types.InlineKeyboardButton("📉 İNİAL (TC)", callback_data="menu_inial_tc"),
        types.InlineKeyboardButton("⚖️ VERGİ (AD)", callback_data="menu_vergi_ad"),
        types.InlineKeyboardButton("⚖️ VERGİ (NO)", callback_data="menu_vergi_no"),
        types.InlineKeyboardButton("⚖️ VERGİ (TC)", callback_data="menu_vergi_tc")
    ]
    
    if sayfa == 1:
        markup.add(*sayfa_1_butonlar)
        markup.row(
            types.InlineKeyboardButton("⬅️ Geri", callback_data="anamenu_sayfa_2"),
            types.InlineKeyboardButton("1/2", callback_data="bos_sayfa_bilgi"),
            types.InlineKeyboardButton("İleri ➡️", callback_data="anamenu_sayfa_2")
        )
        baslik = "✨ Lütfen bir işlem seçin (Sayfa 1/2):"
    else:
        markup.add(*sayfa_2_butonlar)
        markup.row(
            types.InlineKeyboardButton("⬅️ Geri", callback_data="anamenu_sayfa_1"),
            types.InlineKeyboardButton("2/2", callback_data="bos_sayfa_bilgi"),
            types.InlineKeyboardButton("İleri ➡️", callback_data="anamenu_sayfa_1")
        )
        baslik = "✨ Lütfen bir işlem seçin (Sayfa 2/2):"

    markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="anamenu_sayfa_1"))

    try:
        bot.edit_message_text(baslik, chat_id, message_id, reply_markup=markup)
    except Exception:
        sent = bot.send_message(chat_id, baslik, reply_markup=markup)
        if chat_id in kullanici_verileri:
            kullanici_verileri[chat_id]["aktif_mesaj_id"] = sent.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("anamenu_sayfa_"))
def callback_anamenu_sayfa(call):
    user_id = call.from_user.id
    if user_id in engellenenler: return
    sayfa = int(call.data.split("_")[-1])
    ana_menu_gonder(call.message.chat.id, call.message.message_id, sayfa=sayfa)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "bos_sayfa_bilgi")
def callback_bos_bilgi(call):
    bot.answer_callback_query(call.id, "Mevcut sayfadesiniz.")

@bot.callback_query_handler(func=lambda call: call.data == "kontrol_et")
def callback_kontrol(call):
    user_id = call.from_user.id
    if user_id in engellenenler:
        bot.answer_callback_query(call.id, "Botu kullanmanız engellenmiştir.", show_alert=True)
        return
        
    if kullanici_kanalda_mi(user_id):
        bot.answer_callback_query(call.id, "✅ Kanal katılımınız onaylandı!")
        ana_menu_gonder(call.message.chat.id, call.message.message_id, sayfa=1)
    else:
        bot.answer_callback_query(call.id, "❌ Henüz kanalımıza katıldığınızı tespit edemedim!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "iptal")
def callback_iptal(call):
    bot.answer_callback_query(call.id, "❌ İşlem iptal edildi.")
    ana_menu_gonder(call.message.chat.id, call.message.message_id, sayfa=1)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sayfa_"))
def callback_sayfa_degis(call):
    user_id = call.from_user.id
    if user_id in engellenenler: return
    if user_id not in kullanici_verileri or "sonuclar" not in kullanici_verileri[user_id]:
        bot.answer_callback_query(call.id, "❌ Süre aşımı veya sonuç bulunamadı!", show_alert=True)
        return
    
    yeni_sayfa = int(call.data.split("_")[1])
    kullanici_verileri[user_id]["aktif_sayfa"] = yeni_sayfa
    sonuclari_goster(call.message.chat.id, call.message.message_id, user_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "txt_olarak_gonder")
def callback_txt_gonder(call):
    user_id = call.from_user.id
    if user_id in engellenenler: return
    if user_id not in kullanici_verileri or "sonuclar" not in kullanici_verileri[user_id]:
        bot.answer_callback_query(call.id, "❌ Sonuçlar bulunamadı!", show_alert=True)
        return
    
    sonuclar = kullanici_verileri[user_id]["sonuclar"]
    chat_id = call.message.chat.id
    
    txt_icerik = ""
    for idx, sonuc in enumerate(sonuclar[:5000], 1):
        txt_icerik += f"👤 KİŞİ #{idx}\n{sonuc}\n\n{'='*50}\n"
    
    dosya = io.BytesIO(txt_icerik.encode('utf-8'))
    dosya.name = "sorgu_sonuclari.txt"
    
    bot.send_document(chat_id, dosya, caption=f"📊 Toplam {len(sonuclar)} kayıt")
    ana_menu_gonder(chat_id, call.message.message_id, sayfa=1)

def sonuclari_goster(chat_id, message_id, user_id):
    veri = kullanici_verileri.get(user_id, {})
    sonuclar = veri.get("sonuclar", [])
    sayfa = veri.get("aktif_sayfa", 0)
    toplam = len(sonuclar)
    
    if not sonuclar:
        return

    sonuc_metni = sonuclar[sayfa]
    baslik = f"📄 Sonuçlar — Sayfa {sayfa + 1}/{toplam} (1 kayıt)\n\n👤 KİŞİ #{sayfa + 1}\n{sonuc_metni}"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    butonlar = []
    if sayfa > 0:
        butonlar.append(types.InlineKeyboardButton("◀️ Önceki", callback_data=f"sayfa_{sayfa - 1}"))
    if sayfa < toplam - 1:
        butonlar.append(types.InlineKeyboardButton("Sonraki ▶️", callback_data=f"sayfa_{sayfa + 1}"))
        
    if butonlar:
        markup.row(*butonlar)
        
    btn_txt = types.InlineKeyboardButton("📄 Tümünü TXT İndir", callback_data="txt_olarak_gonder")
    btn_iptal = types.InlineKeyboardButton("❌ Kapat / Ana Menü", callback_data="iptal")
    markup.add(btn_txt, btn_iptal)
    
    try:
        bot.edit_message_text(baslik, chat_id, message_id, reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def callback_menu(call):
    user_id = call.from_user.id
    if user_id in engellenenler:
        bot.answer_callback_query(call.id, "Botu kullanmanız engellenmiştir.", show_alert=True)
        return
        
    if not kullanici_kanalda_mi(user_id):
        bot.answer_callback_query(call.id, "Önce kanala katılmalısın!", show_alert=True)
        return
    
    islem = call.data.replace("menu_", "")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ İPTAL", callback_data="iptal"))

    msg_id = call.message.message_id
    chat_id = call.message.chat.id

    if user_id not in kullanici_verileri:
        kullanici_verileri[user_id] = {}
    kullanici_verileri[user_id]["aktif_mesaj_id"] = msg_id
    kullanici_verileri[user_id]["islem"] = islem

    if islem in ["adsoyad", "adsoyadpro", "vergi_ad"]:
        bot.edit_message_text("✏️ Lütfen **AD** giriniz:", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler_by_chat_id(chat_id, ad_girildi_islem)
    elif islem == "dogumtililce":
        bot.edit_message_text("✏️ Lütfen **Doğum Tarihi** giriniz (İsteğe bağlı, direkt geçmek için '-' yazabilirsiniz):", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler_by_chat_id(chat_id, dogumt_girildi_islem)
    elif islem == "soyaddogumt":
        bot.edit_message_text("✏️ Lütfen **Doğum Tarihi** giriniz (İsteğe bağlı, direkt geçmek için '-' yazabilirsiniz):", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler_by_chat_id(chat_id, soyaddogumt_tarih_girildi)
    else:
        ipucu = "TC Kimlik"
        if islem in ["gsmtc", "inial_gsm"]: ipucu = "GSM Numarası"
        elif islem == "plaka": ipucu = "Araç Plakası"
        elif islem == "iban": ipucu = "IBAN Numarası"
        elif islem == "gncloperator": ipucu = "Telefon Numarası"
        elif islem == "bahis": ipucu = "İsim Soyisim"
        elif islem == "ipinfo": ipucu = "IP Adresi"
        elif islem in ["eczane", "universite_ara"]: ipucu = "Arama Terimi / Ad"
        elif islem in ["dcbottoken", "tgtoken"]: ipucu = "Bot Token"
        elif islem == "papara": ipucu = "Papara ID"
        elif islem == "vergi_no": ipucu = "Vergi Numarası"
        
        bot.edit_message_text(f"✏️ Lütfen **{ipucu}** giriniz:", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler_by_chat_id(chat_id, tekli_parametre_sorgula)

def ad_girildi_islem(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    ad = message.text.strip()
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    if user_id not in kullanici_verileri: kullanici_verileri[user_id] = {}
    kullanici_verileri[user_id]["ad"] = ad
    
    msg_id = kullanici_verileri[user_id].get("aktif_mesaj_id")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ İPTAL", callback_data="iptal"))
    
    islem = kullanici_verileri[user_id].get("islem")
    if islem in ["adsoyad", "adsoyadpro"]:
        text = f"✏️ '{ad}' için **SOYAD** giriniz:"
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler_by_chat_id(chat_id, soyad_girildi_islem)
    elif islem == "vergi_ad":
        text = f"✏️ '{ad}' için **SOYAD** giriniz:"
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler_by_chat_id(chat_id, vergi_soyad_girildi)

def soyad_girildi_islem(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    soyad = message.text.strip()
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    veri = kullanici_verileri.get(user_id, {})
    ad = quote(veri.get("ad", ""))
    soyad_en = quote(soyad)
    islem = veri.get("islem")
    
    if islem == "adsoyadpro":
        url = f"https://infolanmam.info/apiv4pub.php?action=adsoyadpro&ad={ad}&soyad={soyad_en}"
        api_sorgu_calistir(chat_id, url, user_id)
    else:
        kullanici_verileri[user_id]["soyad"] = soyad
        msg_id = veri.get("aktif_mesaj_id")
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ İPTAL", callback_data="iptal"))
        bot.edit_message_text(f"✏️ Lütfen **İL** giriniz (İsteğe bağlı, geçmek için '-' yazın):", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler_by_chat_id(chat_id, adsoyad_il_girildi)

def adsoyad_il_girildi(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    il = message.text.strip()
    if il == "-": il = ""
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    veri = kullanici_verileri.get(user_id, {})
    ad = quote(veri.get("ad", ""))
    soyad = quote(veri.get("soyad", ""))
    il_en = quote(il)
    
    url = f"https://infolanmam.info/apiv4pub.php?action=adsoyad&ad={ad}&soyad={soyad}&il={il_en}"
    api_sorgu_calistir(chat_id, url, user_id)

def vergi_soyad_girildi(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    soyad = message.text.strip()
    if soyad == "-": soyad = ""
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    veri = kullanici_verileri.get(user_id, {})
    ad = quote(veri.get("ad", ""))
    soyad_en = quote(soyad)
    url = f"https://infolanmam.info/apiv4pub.php?action=vergi_ad&ad={ad}&soyad={soyad_en}"
    api_sorgu_calistir(chat_id, url, user_id)

def dogumt_girildi_islem(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    dogumt = message.text.strip()
    if dogumt == "-": dogumt = ""
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    if user_id not in kullanici_verileri: kullanici_verileri[user_id] = {}
    kullanici_verileri[user_id]["dogumt"] = dogumt
    msg_id = kullanici_verileri[user_id].get("aktif_mesaj_id")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ İPTAL", callback_data="iptal"))
    bot.edit_message_text("✏️ Lütfen **İL** giriniz (İsteğe bağlı, geçmek için '-' yazın):", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler_by_chat_id(chat_id, dogumt_il_girildi)

def dogumt_il_girildi(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    il = message.text.strip()
    if il == "-": il = ""
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    kullanici_verileri[user_id]["il"] = il
    msg_id = kullanici_verileri[user_id].get("aktif_mesaj_id")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ İPTAL", callback_data="iptal"))
    bot.edit_message_text("✏️ Lütfen **İLÇE** giriniz (İsteğe bağlı, geçmek için '-' yazın):", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler_by_chat_id(chat_id, dogumt_ilce_girildi)

def dogumt_ilce_girildi(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    ilce = message.text.strip()
    if ilce == "-": ilce = ""
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    veri = kullanici_verileri.get(user_id, {})
    dogumt = quote(veri.get("dogumt", ""))
    il = quote(veri.get("il", ""))
    ilce_en = quote(ilce)
    
    url = f"https://infolanmam.info/apiv4pub.php?action=dogumtililce&dogumt={dogumt}&il={il}&ilce={ilce_en}"
    api_sorgu_calistir(chat_id, url, user_id)

def soyaddogumt_tarih_girildi(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    dogumt = message.text.strip()
    if dogumt == "-": dogumt = ""
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    if user_id not in kullanici_verileri: kullanici_verileri[user_id] = {}
    kullanici_verileri[user_id]["dogumt"] = dogumt
    msg_id = kullanici_verileri[user_id].get("aktif_mesaj_id")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ İPTAL", callback_data="iptal"))
    bot.edit_message_text("✏️ Lütfen **SOYAD** giriniz:", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler_by_chat_id(chat_id, soyaddogumt_soyad_girildi)

def soyaddogumt_soyad_girildi(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    soyad = message.text.strip()
    if soyad == "-": soyad = ""
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    veri = kullanici_verileri.get(user_id, {})
    dogumt = quote(veri.get("dogumt", ""))
    soyad_en = quote(soyad)
    
    url = f"https://infolanmam.info/apiv4pub.php?action=soyaddogumt&dogumt={dogumt}&soyad={soyad_en}"
    api_sorgu_calistir(chat_id, url, user_id)

def tekli_parametre_sorgula(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    param = message.text.strip()
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    veri = kullanici_verileri.get(user_id, {})
    islem = veri.get("islem", "tc")
    en_param = quote(param)
    
    urls = {
        "tc": f"https://infolanmam.info/apiv4pub.php?action=tc&tc={en_param}",
        "tcpro": f"https://infolanmam.info/apiv4pub.php?action=tcpro&tc={en_param}",
        "aile": f"https://infolanmam.info/apiv4pub.php?action=aile&tc={en_param}",
        "ailepro": f"https://infolanmam.info/apiv4pub.php?action=ailepro&tc={en_param}",
        "sulale": f"https://infolanmam.info/apiv4pub.php?action=sulale&tc={en_param}",
        "sulalepro": f"https://infolanmam.info/apiv4pub.php?action=sulalepro&tc={en_param}",
        "cocuk": f"https://infolanmam.info/apiv4pub.php?action=cocuk&tc={en_param}",
        "es": f"https://infolanmam.info/apiv4pub.php?action=es&tc={en_param}",
        "kardes": f"https://infolanmam.info/apiv4pub.php?action=kardes&tc={en_param}",
        "adres": f"https://infolanmam.info/apiv4pub.php?action=adres&tc={en_param}",
        "isyeri": f"https://infolanmam.info/apiv4pub.php?action=isyeri&tc={en_param}",
        "tapu": f"https://infolanmam.info/apiv4pub.php?action=tapu&tc={en_param}",
        "iban": f"https://infolanmam.info/apiv4pub.php?action=iban&iban={en_param}",
        "gsmtc": f"https://infolanmam.info/apiv4pub.php?action=gsmtc&gsm={en_param}",
        "tcgsm": f"https://infolanmam.info/apiv4pub.php?action=tcgsm&tc={en_param}",
        "gncloperator": f"https://infolanmam.info/apiv4pub.php?action=gncloperator&numara={en_param}",
        "vesika": f"https://infolanmam.info/apiv4pub.php?action=vesika&tc={en_param}",
        "asi": f"https://infolanmam.info/apiv4pub.php?action=asi&tc={en_param}",
        "plaka": f"https://infolanmam.info/apiv4pub.php?action=plaka&plate={en_param}",
        "bahis": f"https://infolanmam.info/apiv4pub.php?action=bahis&isimsoyisim={en_param}",
        "ipinfo": f"https://infolanmam.info/apiv4pub.php?action=ipinfo&ip={en_param}",
        "eczane": f"https://infolanmam.info/apiv4pub.php?action=eczane&ad={en_param}",
        "dcbottoken": f"https://infolanmam.info/apiv4pub.php?action=dcbottoken&token={en_param}",
        "tgtoken": f"https://infolanmam.info/apiv4pub.php?action=tgtoken&token={en_param}",
        "sgk": f"https://infolanmam.info/apiv4pub.php?action=sgk&tc={en_param}",
        "eokul": f"https://infolanmam.info/apiv4pub.php?action=eokul&tc={en_param}",
        "secmen": f"https://infolanmam.info/apiv4pub.php?action=secmen&tc={en_param}",
        "papara": f"https://infolanmam.info/apiv4pub.php?action=papara&papara_id={en_param}",
        "universite_tc": f"https://infolanmam.info/apiv4pub.php?action=universite_tc&q={en_param}",
        "universite_ara": f"https://infolanmam.info/apiv4pub.php?action=universite_ara&q={en_param}",
        "inial_gsm": f"https://infolanmam.info/apiv4pub.php?action=inial_gsm&gsm={en_param}",
        "inial_tc": f"https://infolanmam.info/apiv4pub.php?action=inial_tc&tc={en_param}",
        "vergi_no": f"https://infolanmam.info/apiv4pub.php?action=vergi_no&no={en_param}",
        "vergi_tc": f"https://infolanmam.info/apiv4pub.php?action=vergi_tc&tc={en_param}"
    }

    url = urls.get(islem)
    if not url: return
    api_sorgu_calistir(chat_id, url, user_id)

def api_sorgu_calistir(chat_id, url, user_id):
    msg_id = kullanici_verileri.get(user_id, {}).get("aktif_mesaj_id")
    
    if msg_id:
        try: bot.edit_message_text("🔍 Aranıyor, lütfen bekleyin...", chat_id, msg_id)
        except: pass

    try:
        yanit = requests.get(url, timeout=1000)
        
        if yanit.status_code == 200:
            try:
                jdata = yanit.json()
                gercek_veriler = []
                
                if isinstance(jdata, dict):
                    res_data = jdata.get("results", jdata)
                    if isinstance(res_data, list): gercek_veriler = res_data
                    elif isinstance(res_data, dict): gercek_veriler = [res_data]
                    else: gercek_veriler = [jdata]
                elif isinstance(jdata, list):
                    gercek_veriler = jdata
            except:
                gercek_veriler = []

            if not gercek_veriler:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="anamenu_sayfa_1"))
                if msg_id: bot.edit_message_text("❌ Kayıt bulunamadı.", chat_id, msg_id, reply_markup=markup)
                return
            
            formatted_results = []
            for kayit in gercek_veriler:
                if isinstance(kayit, dict):
                    metin = ""
                    for k, v in kayit.items():
                        if k in ["id", "data", "success", "developer", "version"]: continue
                        if isinstance(v, list): v_str = ", ".join(map(str, v))
                        elif v is None: v_str = "YOK"
                        else: v_str = str(v)
                        
                        metin += f"├─ {k.upper()}: {v_str}\n"
                    
                    metin += f"├─ DEVELOPER: @lanetliymis\n└─ VERSION: 4.0"
                    if metin.strip(): formatted_results.append(metin.strip())
                else:
                    formatted_results.append(f"├─ SONUÇ: {str(kayit)}\n├─ DEVELOPER: @lanetliymis\n└─ VERSION: 4.0")
            
            if not formatted_results:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="anamenu_sayfa_1"))
                if msg_id: bot.edit_message_text("❌ Kayıt bulunamadı.", chat_id, msg_id, reply_markup=markup)
                return

            kullanici_verileri[user_id]["sonuclar"] = formatted_results
            kullanici_verileri[user_id]["aktif_sayfa"] = 0
            
            sonuclari_goster(chat_id, msg_id, user_id)
            
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="anamenu_sayfa_1"))
            if msg_id: bot.edit_message_text(f"❌ Sunucu Hatası (Kod: {yanit.status_code})", chat_id, msg_id, reply_markup=markup)
    except Exception as e:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="anamenu_sayfa_1"))
        if msg_id: bot.edit_message_text(f"⚠️ Bağlantı Hatası: {e}", chat_id, msg_id, reply_markup=markup)

print("Panel botu aktif ve çalışıyor...")
bot.infinity_polling()
