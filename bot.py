import telebot
from telebot import types
import requests
import json
import re
from urllib.parse import quote
import io
from flask import Flask, jsonify, render_template_string
import threading
import datetime

TOKEN = "8968096720:AAGg7QCldEKlV6liYMf7HmvFMq1Ekjh888Q"
KANAL_ID = "@freedosya"
ADMIN_ID = 8770418133

bot = telebot.TeleBot(TOKEN)
kullanici_verileri = {}
engellenenler = set()

# Anlık logların tutulduğu liste
canli_loglar = []

# --- FLASK WEB SUNUCUSU (CANLI LOG PANELİ) ---
app = Flask(__name__)

HTML_SAYFASI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Telegram Bot Canlı Log Ekranı</title>
    <style>
        body { background: #0b0f19; color: #00ffcc; font-family: monospace; padding: 20px; }
        .header { border-bottom: 2px solid #1f293d; padding-bottom: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        h1 { color: #fff; margin: 0; font-size: 22px; }
        .status { font-size: 14px; color: #10b981; background: rgba(16, 185, 129, 0.1); padding: 5px 10px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.3); }
        .card { background: #111827; border: 1px solid #1f2937; border-left: 4px solid #3b82f6; padding: 15px; margin-bottom: 15px; border-radius: 6px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); }
        .header-info { color: #9ca3af; font-size: 13px; border-bottom: 1px solid #1f2937; padding-bottom: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; }
        .user { color: #f43f5e; font-weight: bold; }
        .zaman { color: #fbbf24; }
        pre { margin: 0; white-space: pre-wrap; word-wrap: break-word; color: #34d399; font-size: 14px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Telegram Bot Canlı Sorgu Paneli</h1>
        <div class="status">● Canlı Akış Aktif</div>
    </div>
    <div id="log-alani">Loglar yükleniyor...</div>

    <script>
        async function loglariGetir() {
            try {
                let res = await fetch('/api/loglar');
                let veri = await res.json();
                let alan = document.getElementById('log-alani');
                
                if (veri.length === 0) {
                    alan.innerHTML = "<p>Henüz bir sorgu yapılmadı...</p>";
                    return;
                }

                let html = "";
                veri.reverse().forEach(item => {
                    html += `
                        <div class="card">
                            <div class="header-info">
                                <span>SORGULAYAN: <span class="user">@${item.yapan}</span></span>
                                <span class="zaman">${item.zaman}</span>
                            </div>
                            <pre>├─ İŞLEM: ${item.islem.toUpperCase()}
├─ ARANAN: ${item.aranan}
${item.sonuc}
└─ VERSION: 4.0</pre>
                        </div>
                    `;
                });
                alan.innerHTML = html;
            } catch (e) {
                console.log("Log çekme hatası:", e);
            }
        }

        setInterval(loglariGetir, 2000);
        loglariGetir();
    </script>
</body>
</html>
"""

@app.route('/')
def anasayfa():
    return render_template_string(HTML_SAYFASI)

@app.route('/api/loglar')
def api_loglar():
    return jsonify(canli_loglar)

def web_sunucuyu_baslat():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


# --- TELEGRAM BOT MANTIĞI ---

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
    kanal_buton = types.InlineKeyboardButton("📢 Kanal", url="https://t.me/freedosya")
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
    ana_menu_gonder(message.chat.id, sent.message_id)

def ana_menu_gonder(chat_id, message_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    butonlar = [
        types.InlineKeyboardButton("🔍 TC SORGU", callback_data="menu_tc"),
        types.InlineKeyboardButton("⭐ TC PRO", callback_data="menu_tcpro"),
        types.InlineKeyboardButton("📝 AD SOYAD", callback_data="menu_adsoyad"),
        types.InlineKeyboardButton("👨‍👩‍👧‍👦 AİLE", callback_data="menu_aile"),
        types.InlineKeyboardButton("⭐ AİLE PRO", callback_data="menu_ailepro"),
        types.InlineKeyboardButton("🌳 SÜLALE", callback_data="menu_sulale"),
        types.InlineKeyboardButton("📱 TC'DEN GSM", callback_data="menu_tcgsm"),
        types.InlineKeyboardButton("📞 GSM'DEN TC", callback_data="menu_gsmtc"),
        types.InlineKeyboardButton("📚 E-OKUL", callback_data="menu_eokul"),
        types.InlineKeyboardButton("🏠 ADRES", callback_data="menu_adres"),
        types.InlineKeyboardButton("📜 TAPU", callback_data="menu_tapu"),
        types.InlineKeyboardButton("🗺️ ADA PARSEL", callback_data="menu_adaparsel")
    ]
    
    markup.add(*butonlar)
    baslik = "✨ Lütfen bir işlem seçin:"

    try:
        bot.edit_message_text(baslik, chat_id, message_id, reply_markup=markup)
    except Exception:
        sent = bot.send_message(chat_id, baslik, reply_markup=markup)
        if chat_id in kullanici_verileri:
            kullanici_verileri[chat_id]["aktif_mesaj_id"] = sent.message_id

@bot.callback_query_handler(func=lambda call: call.data == "kontrol_et")
def callback_kontrol(call):
    user_id = call.from_user.id
    if user_id in engellenenler:
        bot.answer_callback_query(call.id, "Botu kullanmanız engellenmiştir.", show_alert=True)
        return
        
    if kullanici_kanalda_mi(user_id):
        bot.answer_callback_query(call.id, "✅ Kanal katılımınız onaylandı!")
        ana_menu_gonder(call.message.chat.id, call.message.message_id)
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
