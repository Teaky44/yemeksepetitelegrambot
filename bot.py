import asyncio
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")  # Railway’de ENV olarak eklenecek
GROUP_ID = os.getenv("GROUP_ID")     # Gruptaki ID’yi buraya ENV olarak ekle (örn. -1001234567890)
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

# ✅ Kod sorgulama & davet linki gönderme
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("❌ Kod sadece sayılardan oluşmalı!")
        return

    df = read_codes()
    code = int(text)

    # ✅ Kod var mı?
    if code not in df["Kod"].values:
        await update.message.reply_text("❌ Kod bulunamadı!")
        return

    # ✅ Kod kullanılmış mı?
    row = df[df["Kod"] == code].iloc[0]
    if pd.notna(row["TelegramID"]):
        await update.message.reply_text("❌ Bu kod zaten kullanıldı.")
        return

    # ✅ Tek kullanımlık davet linki oluştur
    try:
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            name=f"Kod {code} - {user_name}",
            member_limit=1,        # 🔑 sadece 1 kişi kullanabilir
            creates_join_request=False
        )

        # ✅ ID kaydet
        df.loc[df["Kod"] == code, "TelegramID"] = user_id
        write_codes(df)

        await update.message.reply_text(f"✅ Kod onaylandı!\n👉 Gruba katılmak için link: {invite_link.invite_link}")

    except Exception as e:
        await update.message.reply_text(f"❌ Davet linki oluşturulamadı: {e}")

# ✅ Excel kontrol task’ı
async def excel_watcher(app):
    await asyncio.sleep(5)  # Bot başlar başlamaz excel kontrolüne başla
    while True:
        await asyncio.sleep(15)  # 15 sn’de bir Excel’i kontrol et
        try:
            df = read_codes()
            for index, row in df.iterrows():
                if pd.isna(row["TelegramID"]):
                    continue
                if row["Kod"] not in df["Kod"].values:
                    continue
        except Exception as e:
            print(f"[Excel Watcher] Hata: {e}")

# ✅ Bot başlat
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_code))

    # Excel watcher
    asyncio.create_task(excel_watcher(app))

    print("✅ Bot çalışıyor...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
