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
der(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Henüz kanalımıza katıldığınızı tespit edemedim!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "iptal")
def callback_iptal(call):
    bot.answer_callback_query(call.id, "❌ İşlem iptal edildi.")
    ana_menu_gonder(call.message.chat.id, call.message.message_id)

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
    ana_menu_gonder(chat_id, call.message.message_id)

def sonuclari_goster(chat_id, message_id, user_id):
    veri = kullanici_verileri.get(user_id, {})
    sonuclar = veri.get("sonuclar", [])
    sayfa = veri.get("aktif_sayfa", 0)
    toplam = len(sonuclar)
    
    if not sonuclar:
        return

    sonuc_metni = sonuclar[sayfa]
    baslik = f"📄 Sonuçlar — Sayfa {sayfa + 1}/{toplam} ({toplam} kayıt)\n\n👤 KİŞİ #{sayfa + 1}\n{sonuc_metni}"
    
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

    if islem == "adsoyad":
        bot.edit_message_text("✏️ Lütfen **AD** giriniz:", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler_by_chat_id(chat_id, ad_girildi_islem)
    elif islem == "adaparsel":
        bot.edit_message_text("✏️ Lütfen **İL** giriniz:", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler_by_chat_id(chat_id, adaparsel_il_girildi)
    else:
        ipucu = "TC Kimlik"
        if islem == "tcgsm": ipucu = "TC Kimlik"
        elif islem == "gsmtc": ipucu = "GSM Numarası (Örn: 5550000000)"
        
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
    
    text = f"✏️ '{ad}' için **SOYAD** giriniz:"
    bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler_by_chat_id(chat_id, soyad_girildi_islem)

def soyad_girildi_islem(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    soyad = message.text.strip()
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    veri = kullanici_verileri.get(user_id, {})
    ad = veri.get("ad", "")
    url = f"https://apiv2.ajaxsystems.fun/adsoyad.php?ad={quote(ad)}&soyad={quote(soyad)}"
    api_sorgu_calistir(chat_id, url, user_id, "adsoyad", f"{ad} {soyad}")

def adaparsel_il_girildi(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    il = message.text.strip()
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    if user_id not in kullanici_verileri: kullanici_verileri[user_id] = {}
    kullanici_verileri[user_id]["il"] = il
    
    msg_id = kullanici_verileri[user_id].get("aktif_mesaj_id")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ İPTAL", callback_data="iptal"))
    
    bot.edit_message_text(f"✏️ '{il}' için **İLÇE** giriniz:", chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler_by_chat_id(chat_id, adaparsel_ilce_girildi)

def adaparsel_ilce_girildi(message):
    if message.text and message.text.startswith("/"): return
    user_id = message.from_user.id
    if user_id in engellenenler: return
    chat_id = message.chat.id
    ilce = message.text.strip()
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    veri = kullanici_verileri.get(user_id, {})
    il = veri.get("il", "")
    url = f"https://apiv2.ajaxsystems.fun/adaparsel.php?il={quote(il)}&ilce={quote(ilce)}"
    api_sorgu_calistir(chat_id, url, user_id, "adaparsel", f"İl: {il}, İlçe: {ilce}")

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
        "tc": f"https://apiv2.ajaxsystems.fun/tc.php?tc={en_param}",
        "tcpro": f"https://apiv2.ajaxsystems.fun/tcpro.php?tc={en_param}",
        "aile": f"https://apiv2.ajaxsystems.fun/aile.php?tc={en_param}",
        "ailepro": f"https://apiv2.ajaxsystems.fun/ailepro.php?tc={en_param}",
        "sulale": f"https://apiv2.ajaxsystems.fun/sulale.php?tc={en_param}",
        "tcgsm": f"https://apiv2.ajaxsystems.fun/tcgsm.php?tc={en_param}",
        "gsmtc": f"https://apiv2.ajaxsystems.fun/gsmtc.php?gsm={en_param}&auth=fire",
        "eokul": f"https://apiv2.ajaxsystems.fun/eokul.php?tc={en_param}",
        "adres": f"https://apiv2.ajaxsystems.fun/adres.php?tc={en_param}",
        "tapu": f"https://apiv2.ajaxsystems.fun/tapu.php?tc={en_param}"
    }

    url = urls.get(islem)
    if not url: return
    api_sorgu_calistir(chat_id, url, user_id, islem, param)

def api_sorgu_calistir(chat_id, url, user_id, islem_adi, aranan_deger):
    msg_id = kullanici_verileri.get(user_id, {}).get("aktif_mesaj_id")
    
    if msg_id:
        try: bot.edit_message_text("🔍 Aranıyor, lütfen bekleyin...", chat_id, msg_id)
        except: pass

    try:
        yanit = requests.get(url, timeout=30)
        
        if yanit.status_code == 200:
            try:
                jdata = yanit.json()
                gercek_veriler = []
                
                if isinstance(jdata, dict):
                    if "data" in jdata and jdata["data"]:
                        res = jdata["data"]
                    elif "results" in jdata and jdata["results"]:
                        res = jdata["results"]
                    elif "result" in jdata and jdata["result"]:
                        res = jdata["result"]
                    else:
                        res = jdata

                    if isinstance(res, list):
                        gercek_veriler = res
                    elif isinstance(res, dict):
                        gercek_veriler = [res]
                    else:
                        gercek_veriler = [jdata]
                elif isinstance(jdata, list):
                    gercek_veriler = jdata
            except Exception as e:
                gercek_veriler = []

            if not gercek_veriler:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="iptal"))
                if msg_id: bot.edit_message_text("❌ Kayıt bulunamadı.", chat_id, msg_id, reply_markup=markup)
                return
            
            formatted_results = []
            ilk_metin_log = ""
            for idx, kayit in enumerate(gercek_veriler):
                if isinstance(kayit, dict):
                    metin = ""
                    for k, v in kayit.items():
                        if k.lower() in ["status", "success", "developer", "version", "message"]: 
                            continue
                        
                        if isinstance(v, list): 
                            v_str = ", ".join(map(str, v))
                        elif v is None or v == "": 
                            v_str = "YOK"
                        else: 
                            v_str = str(v)
                        
                        metin += f"├─ {k.upper()}: {v_str}\n"
                    
                    if metin.strip():
                        metin += "├─ DEVELOPER: @lanetliymis\n└─ VERSION: 4.0"
                        formatted_results.append(metin.strip())
                        if idx == 0:
                            ilk_metin_log = metin.strip()
                else:
                    res_str = f"├─ SONUÇ: {str(kayit)}\n├─ DEVELOPER: @lanetliymis\n└─ VERSION: 4.0"
                    formatted_results.append(res_str)
                    if idx == 0:
                        ilk_metin_log = res_str
            
            if not formatted_results:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="iptal"))
                if msg_id: bot.edit_message_text("❌ Kayıt bulunamadı.", chat_id, msg_id, reply_markup=markup)
                return

            kullanici_verileri[user_id]["sonuclar"] = formatted_results
            kullanici_verileri[user_id]["aktif_sayfa"] = 0
            
            sonuclari_goster(chat_id, msg_id, user_id)

            # Kullanıcı adını al
            try:
                chat_info = bot.get_chat(user_id)
                username = chat_info.username or chat_info.first_name or str(user_id)
            except:
                username = str(user_id)

            # FLASK WEB PANELİNE LOGU EKLE
            zaman_str = datetime.datetime.now().strftime("%H:%M:%S")
            canli_loglar.append({
                "yapan": username,
                "islem": islem_adi,
                "aranan": aranan_deger,
                "sonuc": ilk_metin_log,
                "zaman": zaman_str
            })
            
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="iptal"))
            if msg_id: bot.edit_message_text(f"❌ Sunucu Hatası (Kod: {yanit.status_code})", chat_id, msg_id, reply_markup=markup)
    except Exception as e:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="iptal"))
        if msg_id: bot.edit_message_text(f"⚠️ Bağlantı Hatası: {e}", chat_id, msg_id, reply_markup=markup)

if __name__ == "__main__":
    # Web sunucusunu arka planda başlat
    t = threading.Thread(target=web_sunucuyu_baslat)
    t.daemon = True
    t.start()
    print("🚀 Panel botu ve Canlı Web Log sunucusu aktif! http://localhost:5000 adresinden izleyebilirsin.")
    bot.infinity_polling()
