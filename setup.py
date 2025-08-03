import pandas as pd
import os

EXCEL_FILE = "kodlar.xlsx"

def setup_excel():
    if not os.path.exists(EXCEL_FILE):
        # Eğer Excel hiç yoksa sıfırdan oluştur
        df = pd.DataFrame(columns=["Kod", "İsim", "ID"])
        df.to_excel(EXCEL_FILE, index=False)
        print(f"✅ {EXCEL_FILE} oluşturuldu (boş).")
    else:
        # Excel varsa oku
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
        
        # Eğer ID sütunu yoksa ekle
        if "ID" not in df.columns:
            df["ID"] = None
            df.to_excel(EXCEL_FILE, index=False)
            print(f"✅ {EXCEL_FILE} dosyasına 'ID' sütunu eklendi.")
        else:
            print("ℹ Excel zaten hazır, değişiklik yapılmadı.")

if __name__ == "__main__":
    setup_excel()

