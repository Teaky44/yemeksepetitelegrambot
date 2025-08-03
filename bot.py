import pandas as pd
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import asyncio

TOKEN = "7618800446:AAGX5gmYeKIxgJ7ZjI_4wToBGCHhQl6zrGw"
GROUP_ID = -1002783764688
EXCEL_FILE = "kodlar.xlsx"

# ✅ SQLite (kod – user_id – isim)
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (code TEXT PRIMARY KEY, user_id INTEGER, name TEXT)")
conn.commit()

# ✅ Excel okuma
def read_codes():
    return pd.read_excel(EXCEL_FILE, sheet_name="Kodlar", engine="openpyxl")

def read_admins():
    return pd.read_excel(EXCEL_FILE, sheet_name="Adminler", engine="openpyxl")

def is_admin(user_id):
    admins = read_admins()
    return user_id in admins["AdminID"].values

# ✅ Kullanıcı kod girdiğinde
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    df = read_codes()

    if code not in df["Kod"].values:
        await update.message.reply_text("❌ Kod geçerli değil.")
        return

    # Kod daha önce kullanıldı mı?
    cursor.execute("SELECT user_id FROM users WHERE code=?", (code,))
    used = cursor.fetchone()
    if used:
        await update.message.reply_text("❌ Bu kod zaten kullanıldı.")
        return

    # Excel'den isim bul
    name = df.loc[df["Kod"] == code, "İsim"].values[0]

    # Kullanıcıyı gruba ekle
    try:
        await context.bot.add_chat_members(chat_id=GROUP_ID, user_ids=[update.message.from_user.id])
        await update.message.reply_text("✅ Kod onaylandı, gruba eklendin.")
    except Exception as e:
        await update.message.reply_text("🚫 Gruba eklenirken hata oluştu.")
        print(f"Gruba ekleme hatası: {e}")
        return

    # DB kaydı
    cursor.execute("INSERT INTO users (code, user_id, name) VALUES (?, ?, ?)", (code, update.message.from_user.id, name))
    conn.commit()

    # 📢 Grupta hoş geldin
    await context.bot.send_message(chat_id=GROUP_ID, text=f"🎉 {name} – {code} ile aramıza katıldı! 🛵")

    # 📩 Kullanıcıya DM + GIF gönder
    with open("welcome.gif", "rb") as gif_file:
        await context.bot.send_animation(
            chat_id=update.message.from_user.id,
            animation=gif_file,
            caption=(f"🎉 Hoş geldin {name}!\n\n✅ Kodun: {code}\n"
                     f"📦 Artık *Yemeksepeti Kurye Topluluğu*’ndasın.\n\n"
                     "📜 Grup Kuralları:\n"
                     "1️⃣ Kod tek seferliktir, başkasına verme.\n"
                     "2️⃣ Kod silinirse gruptan çıkarsın.\n"
                     "3️⃣ Spam/küfür, reklam yasak.\n"
                     "4️⃣ Burada sadece bilgi & destek paylaşımları var.\n\n"
                     "🛵 Güvenli sürüşler ve keyifli sohbetler!"),
            parse_mode="Markdown"
        )

# ✅ /duyuru komutu (sadece admin)
async def duyuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Bu komutu sadece yöneticiler kullanabilir.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("❗ Kullanım: /duyuru <mesaj>")
        return

    mesaj = " ".join(context.args)
    await context.bot.send_message(chat_id=GROUP_ID, text=f"📢 *Yönetici Duyurusu:*\n{mesaj}", parse_mode="Markdown")

# ✅ Excel watcher (kod silindi mi?)
async def excel_watcher(app):
    while True:
        await asyncio.sleep(60)
        df = read_codes()
        db_users = cursor.execute("SELECT code, user_id, name FROM users").fetchall()

        for code, user_id, name in db_users:
            if code not in df["Kod"].values:
                try:
                    await app.bot.ban_chat_member(GROUP_ID, user_id)
                    await app.bot.unban_chat_member(GROUP_ID, user_id)
                    await app.bot.send_message(chat_id=GROUP_ID, text=f"❌ {name} – {code} kodu iptal edildi, gruptan çıkarıldı.")
                except Exception as e:
                    print(f"Çıkarma hatası: {e}")

                cursor.execute("DELETE FROM users WHERE code=?", (code,))
                conn.commit()

# ✅ Bot başlat
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))
app.add_handler(CommandHandler("duyuru", duyuru))

# ✅ Watcher başlat
import asyncio
import nest_asyncio

nest_asyncio.apply()

async def on_start():
    asyncio.create_task(excel_watcher(app))

if __name__ == "__main__":
    app.run_polling(
        poll_interval=2.0,
        allowed_updates=telegram.constants.Update.ALL_TYPES,
        close_loop=False,       # 🔴 Railway için kritik
        stop_signals=None,
        before_start=on_start   # 🔴 Excel watcher başlıyor
    )
