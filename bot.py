import os
import random
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageEntity,
)

# Bot Token ve Admin ID
TOKEN = "8668738139:AAFAjyGvCHHuhRPJJVFilnmuo6h-MiD46Z8"
ADMIN_ID = 8770418133
CHANNEL_USERNAME = "@freedosya"

bot = telebot.TeleBot(TOKEN)

# Veritabanı Hafızası
user_orders = {}
user_balances = {}

# Senden gelen özel emoji ID tanımları
CUSTOM_EMOJIS = {
    "🎁": "5917820826232560322",
    "⭐": "5985827110764158062",
    "👤": "5920326316879517449",
    "💡": "5917882875625084524",
    "💎": "5917954451255072374",
    "✈️": "5985748293819307278",
}


def build_entities(text):
  entities = []
  text_utf16 = text.encode("utf-16-le")

  for char, eid in CUSTOM_EMOJIS.items():
    char_utf16 = char.encode("utf-16-le")
    pos = 0
    while True:
      idx = text_utf16.find(char_utf16, pos)
      if idx == -1:
        break
      offset_utf16 = idx // 2
      length_utf16 = len(char_utf16) // 2

      entities.append(
          MessageEntity(
              type="custom_emoji",
              offset=offset_utf16,
              length=length_utf16,
              custom_emoji_id=eid,
          )
      )
      pos = idx + len(char_utf16)
  return entities


def send_or_edit_msg(call_or_message, text, reply_markup=None):
  ents = build_entities(text)
  chat_id = (
      call_or_message.message.chat.id
      if hasattr(call_or_message, "message")
      else call_or_message.chat.id
  )

  if hasattr(call_or_message, "message"):
    try:
      return bot.edit_message_text(
          text,
          chat_id,
          call_or_message.message.message_id,
          entities=ents,
          reply_markup=reply_markup,
      )
    except Exception:
      return bot.send_message(
          chat_id, text, entities=ents, reply_markup=reply_markup
      )
  else:
    return bot.send_message(
        chat_id, text, entities=ents, reply_markup=reply_markup
    )


def check_membership(user_id):
  try:
    member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
    return member.status in ["member", "creator", "administrator"]
  except Exception:
    return False


@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  if not check_membership(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            "📢 Kanalımıza Katıl", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "✅ Katıldım, Kontrol Et", callback_data="check_sub"
        )
    )
    send_or_edit_msg(
        message,
        "⚠️ **Kanal Zorunluluğu!**\nBotu kullanabilmek için kanalımıza katılmalısınız.",
        reply_markup=markup,
    )
    return
  show_main_menu(message)


def show_main_menu(call_or_message):
  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton(
          "Brawl Stars Ürünleri", callback_data="cat_bs"
      )
  )
  markup.add(
      InlineKeyboardButton(
          "Telegram Üye Basma", callback_data="cat_tg"
      )
  )
  markup.add(
      InlineKeyboardButton(
          "Discord Hesap & Boost", callback_data="cat_dc"
      )
  )
  markup.add(
      InlineKeyboardButton(
          "Gmail Hesap Hizmetleri", callback_data="cat_gmail"
      )
  )
  markup.add(
      InlineKeyboardButton(
          "Cüzdan / Bakiyem", callback_data="check_balance"
      )
  )

  text = "👤 Ana Menü\n\nAşağıdaki butonlardan birini seç: 🎁"
  send_or_edit_msg(call_or_message, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
  if check_membership(call.from_user.id):
    bot.answer_callback_query(call.id, "✅ Kanal kontrolü başarılı!")
    show_main_menu(call)
  else:
    bot.answer_callback_query(
        call.id, "❌ Hala kanala katılmadın!", show_alert=True
    )


@bot.callback_query_handler(func=lambda call: call.data == "check_balance")
def callback_check_balance(call):
  user_id = call.from_user.id
  balance = user_balances.get(user_id, 0.0)

  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton("🏠 Ana Menüye Dön", callback_data="main_menu")
  )

  text = f"⭐ Hesap Bakiyeniz\n\nGüncel Bakiyeniz: {balance} TL 🎁"
  send_or_edit_msg(call, text, reply_markup=markup)


@bot.message_handler(commands=["para"])
def add_money_command(message):
  if message.from_user.id != ADMIN_ID:
    bot.reply_to(message, "❌ Bu komutu sadece admin kullanabilir!")
    return

  args = message.text.split()
  if len(args) < 3:
    bot.reply_to(message, "⚠️ Örnek kullanım: `/para [ID] [Miktar]`")
    return

  target = args[1]
  try:
    amount = float(args[2])
  except ValueError:
    bot.reply_to(message, "⚠️ Miktar sayı olmalıdır!")
    return

  if target.isdigit():
    target_id = int(target)
    user_balances[target_id] = user_balances.get(target_id, 0.0) + amount
    bot.reply_to(
        message,
        f"✅ Başarılı! `{target_id}` ID'li kullanıcıya `{amount} TL` eklendi.",
    )
    try:
      bot.send_message(
          target_id,
          f"🎉 Hesabınıza `{amount} TL` bakiye eklendi! ⭐\nGüncel Bakiye:"
          f" `{user_balances[target_id]} TL`",
      )
    except Exception:
      pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def callback_categories(call):
  markup = InlineKeyboardMarkup(row_width=1)

  if call.data == "cat_bs":
    markup.add(
        InlineKeyboardButton(
            "Brawl Stars Random (250 TL)", callback_data="buy_bs_random"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "Brawl Stars Kesin Girişli (500 TL)",
            callback_data="buy_bs_kesin",
        )
    )
    text = "👤 Brawl Stars Ürün Kategorisi 🎁"

  elif call.data == "cat_tg":
    markup.add(
        InlineKeyboardButton(
            "500 Telegram Üye (100 TL)", callback_data="buy_tg_500"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "1K Telegram Üye (250 TL)", callback_data="buy_tg_1k"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "10K Telegram Üye (3.000 TL)", callback_data="buy_tg_10k"
        )
    )
    text = "⭐ Telegram Üye Basma Hizmetleri 🎁"

  elif call.data == "cat_dc":
    markup.add(
        InlineKeyboardButton(
            "2024 Tarihli Discord (100 TL)", callback_data="buy_dc_2024"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "2017 Tarihli Discord (500 TL)", callback_data="buy_dc_2017"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "4X Boost 1 Aylık (150 TL)", callback_data="buy_dc_boost4"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "14X Boost 1 Aylık (300 TL)", callback_data="buy_dc_boost14"
        )
    )
    text = "💎 Discord Hesap ve Boost Hizmetleri 🎁"

  elif call.data == "cat_gmail":
    markup.add(
        InlineKeyboardButton(
            "Random Gmail Hesap (50 TL)", callback_data="buy_gmail_random"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "Kesin Girişli Gmail (100 TL)", callback_data="buy_gmail_kesin"
        )
    )
    text = "👤 Gmail Hesap Hizmetleri 🎁"

  markup.add(
      InlineKeyboardButton("🏠 Ana Menüye Dön", callback_data="main_menu")
  )
  send_or_edit_msg(call, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def callback_main_menu(call):
  show_main_menu(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def callback_buy(call):
  data = call.data
  user_id = call.from_user.id

  # Tüm ürünlerin fiyatları ve dosya eşleşmeleri
  product_prices = {
      "buy_bs_random": ("bs_random.txt", "Brawl Stars Random", 250.0),
      "buy_bs_kesin": ("bs_kesin.txt", "Brawl Stars Kesin Girişli", 500.0),
      "buy_gmail_random": ("gmail_random.txt", "Random Gmail", 50.0),
      "buy_gmail_kesin": ("gmail_kesin.txt", "Kesin Girişli Gmail", 100.0),
      "buy_tg_500": (None, "Telegram 500 Üye", 100.0),
      "buy_tg_1k": (None, "Telegram 1K Üye", 250.0),
      "buy_tg_10k": (None, "Telegram 10K Üye", 3000.0),
      "buy_dc_2024": (None, "2024 Tarihli Discord", 100.0),
      "buy_dc_2017": (None, "2017 Tarihli Discord", 500.0),
      "buy_dc_boost4": (None, "4X Boost 1 Aylık", 150.0),
      "buy_dc_boost14": (None, "14X Boost 1 Aylık", 300.0),
  }

  if data not in product_prices:
    return

  filename, prod_name, price = product_prices[data]
  user_balance = user_balances.get(user_id, 0.0)

  # Bakiye kontrolü (Yetersizse uyarı ver)
  if user_balance < price:
    bot.answer_callback_query(
        call.id,
        f"❌ Yetersiz Bakiye! Gerekli: {price} TL, Bakiyeniz: {user_balance} TL",
        show_alert=True,
    )
    return

  # Eğer ürün stoklu dosya ürünüyse (Brawl Stars / Gmail)
  if filename:
    if os.path.exists(filename):
      with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

      if lines:
        # Bakiyeden düşüş yapılıyor
        user_balances[user_id] -= price

        item = lines[0].strip()
        with open(filename, "w", encoding="utf-8") as f:
          f.writelines(lines[1:])

        bot.answer_callback_query(call.id, "✅ Satın alım başarılı!")
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🏠 Ana Menüye Dön", callback_data="main_menu")
        )
        text = (
            f"🎁 Ürününüz Başarıyla Teslim Edildi!\n\n"
            f"⭐ **{prod_name}**\n"
            f"💰 Kesilen Tutar: `{price} TL`\n"
            f"💎 Kalan Bakiye: `{user_balances[user_id]} TL`\n\n"
            f"Ürün Bilgisi:\n`{item}`"
        )
        send_or_edit_msg(call, text, reply_markup=markup)
        return
      else:
        bot.answer_callback_query(
            call.id, "❌ Bu üründe stok kalmadı!", show_alert=True
        )
        return
    else:
      bot.answer_callback_query(
          call.id, "❌ Stok dosyası bulunamadı!", show_alert=True
      )
      return

  # Stoksuz hizmetler (Discord/Telegram üye vb.) için bakiye düşme ve onay süreci
  user_orders[user_id] = prod_name
  user_balances[user_id] -= price  # Bakiyeden düş

  markup = InlineKeyboardMarkup(row_width=1)
  markup.add(
      InlineKeyboardButton("🏠 Ana Menüye Dön", callback_data="main_menu")
  )

  bot.answer_callback_query(call.id, "✅ Siparişiniz alındı!")
  text = (
      f"🎉 **Siparişiniz Başarıyla Oluşturuldu!**\n\n"
      f"🎁 **Seçilen Ürün:** {prod_name}\n"
      f"💰 **Ödenen Tutar:** `{price} TL`\n"
      f"💎 **Kalan Bakiye:** `{user_balances[user_id]} TL`\n\n"
      "Hizmetiniz en kısa sürede işleme alınacaktır. Bizi tercih ettiğiniz için teşekkürler! ⭐"
  )
  send_or_edit_msg(call, text, reply_markup=markup)


print("🚀 Bot bakiye düşme sistemiyle aktif!")
bot.infinity_polling()
