import logging
import pandas as pd
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7618800446:AAGX5gmYeKIxgJ7ZjI_4wToBGCHhQl6zrGw"
GROUP_ID = -1002783764688
EXCEL_FILE = "kodlar.xlsx"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def read_codes():
    return pd.read_excel(EXCEL_FILE, engine="openpyxl")

def save_codes(df):
    df.to_excel(EXCEL_FILE, index=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📥 Hoş geldin! Bana *kodunu* gönder, seni gruba ekleyeyim.", parse_mode="Markdown")

async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    user_id = update.message.from_user.id
    user_name = update.message.from_user.full_name

    try:
        df = read_codes()
    except Exception as e:
        await update.message.reply_text(f"❌ Excel okunamadı: {e}")
        return

    if "Kod" not in df.columns or "İsim" not in df.columns:
        await update.message.reply_text("❌ Excel'de 'Kod' ve 'İsim' sütunları olmalı!")
        return

    matched = df[df["Kod"].astype(str) == user_message]

    if not matched.empty:
        row_index = matched.index[0]
        if not pd.isna(df.loc[row_index, "ID"]):
            await update.message.reply_text("🚫 Bu kod zaten kullanılmış.")
            return

        isim = df.loc[row_index, "İsim"]
        try:
            await context.bot.add_chat_members(chat_id=GROUP_ID, user_ids=[user_id])
            await update.message.reply_text(f"✅ {isim} ({user_message}) gruba eklendi!")

            await context.bot.send_message(chat_id=GROUP_ID, text=f"👋 {isim} - {user_message} katıldı!")

            df.loc[row_index, "ID"] = user_id
            save_codes(df)

        except Exception as e:
            await update.message.reply_text(f"❌ Gruba eklenirken hata: {e}")
    else:
        await update.message.reply_text("🚫 Bu kod geçerli değil ya da silinmiş.")

async def excel_watcher(app):
    last_ids = set()
    while True:
        try:
            df = read_codes()
            if "ID" in df.columns:
                current_ids = set(df["ID"].dropna().astype(int))
                removed_ids = last_ids - current_ids
                for uid in removed_ids:
                    try:
                        await app.bot.ban_chat_member(GROUP_ID, uid)
                        await app.bot.unban_chat_member(GROUP_ID, uid)
                        logging.info(f"❌ {uid} ID'li kullanıcı gruptan çıkarıldı.")
                    except Exception as e:
                        logging.error(f"❌ {uid} gruptan atılamadı: {e}")
                last_ids = current_ids
        except Exception as e:
            logging.error(f"Excel watcher hatası: {e}")

        await asyncio.sleep(30)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))

    # Excel watcher'ı async olarak çalıştır
    asyncio.create_task(excel_watcher(app))

    print("✅ Bot polling başlatılıyor...")
    app.run_polling()   # 🔥 asyncio.run() yok!

if __name__ == "__main__":
    main()
