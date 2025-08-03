import asyncio
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
EXCEL_FILE = "kodlar.xlsx"

# ✅ Excel okuma
def read_codes():
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
    if "Kod" not in df.columns or "İsim" not in df.columns:
        raise ValueError("❌ Excel'de 'Kod' ve 'İsim' sütunları olmalı!")
    if "TelegramID" not in df.columns:
        df["TelegramID"] = None
    return df

# ✅ Excel yazma
def write_codes(df):
    df.to_excel(EXCEL_FILE, index=False)

# ✅ Kod sorgulama
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("❌ Kod sadece sayılardan oluşmalı!")
        return

    df = read_codes()
    code = int(text)

    if code not in df["Kod"].values:
        await update.message.reply_text("❌ Kod bulunamadı!")
        return

    row = df[df["Kod"] == code].iloc[0]
    if pd.notna(row["TelegramID"]):
        await update.message.reply_text("❌ Bu kod zaten kullanıldı.")
        return

    try:
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            name=f"Kod {code} - {user_name}",
            member_limit=1,
            creates_join_request=False
        )

        df.loc[df["Kod"] == code, "TelegramID"] = user_id
        write_codes(df)

        await update.message.reply_text(f"✅ Kod onaylandı!\n👉 Gruba katılmak için link: {invite_link.invite_link}")

    except Exception as e:
        await update.message.reply_text(f"❌ Davet linki oluşturulamadı: {e}")

# ✅ Excel kontrol task’ı
async def excel_watcher(app):
    await asyncio.sleep(5)
    while True:
        await asyncio.sleep(15)
        try:
            df = read_codes()
            # Excel’den silinen kullanıcıları gruptan atma kodu buraya gelecek
        except Exception as e:
            print(f"[Excel Watcher] Hata: {e}")

# ✅ Botu başlat
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_code))

    asyncio.create_task(excel_watcher(app))

    print("✅ Bot çalışıyor...")
    await app.run_polling(close_loop=False)  # ✅ Railway’de loop çakışmasını engeller

if __name__ == "__main__":
    asyncio.run(main())  # ✅ artık loop çakışması yaşamayacaksın
