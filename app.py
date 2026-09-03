import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# ---------------------------------------------------------
# GOOGLE DRIVE ENTEGRASYONU
# ---------------------------------------------------------
DRIVE_FILE_ID = "1UMEYiCL4N8eLzd69yZjvBiNWTeL6yr1q"
LOCAL_DB_PATH = "budget.db"

def get_drive_service():
    """Streamlit Secrets kullanarak Google Drive servisine bağlanır."""
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build('drive', 'v3', credentials=credentials)

def download_db_from_drive():
    """Uygulama açıldığında Drive'dan güncel DB'yi indirir."""
    try:
        service = get_drive_service()
        request = service.files().get_media(fileId=DRIVE_FILE_ID)
        with open(LOCAL_DB_PATH, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        return True
    except Exception as e:
        st.error(f"Drive'dan veritabanı indirilemedi: {e}")
        return False

def upload_db_to_drive():
    """Veri eklendiğinde veya silindiğinde yerel DB'yi Drive'a yedekler."""
    try:
        service = get_drive_service()
        media = MediaFileUpload(LOCAL_DB_PATH, mimetype='application/x-sqlite3', resumable=True)
        service.files().update(fileId=DRIVE_FILE_ID, media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"Drive'a güncel veritabanı yüklenemedi: {e}")
        return False

# Page Configuration
st.set_page_config(
    page_title="POL.Bütçe",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Uygulama oturumunda veri henüz çekilmediyse Drive'dan indir
if "db_synced" not in st.session_state:
    with st.spinner("Google Drive ile senkronize olunuyor..."):
        if download_db_from_drive():
            st.session_state["db_synced"] = True

# Custom CSS & Fonts
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Righteous&display=swap');
    
    /* Logo Wrapper */
    .logo-container {
        text-align: center;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    
    .budget-logo-svg {
        width: 75px;
        height: 75px;
        filter: drop-shadow(0px 4px 6px rgba(178, 34, 34, 0.25));
    }

    /* Main Title Styling */
    .main-title-container {
        text-align: center;
        margin-bottom: 25px;
    }
    .main-title {
        font-family: 'Righteous', 'Poppins', sans-serif;
        font-size: 42px;
        font-weight: 800;
        color: #b22222;
        letter-spacing: 1.5px;
        margin-top: 0px;
        margin-bottom: 10px;
        text-shadow: 1px 2px 4px rgba(0,0,0,0.1);
    }
    .main-title-divider {
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, rgba(178,34,34,0.1) 0%, rgba(178,34,34,0.8) 50%, rgba(178,34,34,0.1) 100%);
        margin-bottom: 20px;
    }

    /* Tabs Styling (Sekme Butonları) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px !important;
        border-bottom: 2px solid #e0e0e0 !important;
        padding-bottom: 8px !important;
    }

    .stTabs [data-baseweb="tab"] {
        height: 52px !important;
        background-color: #f1f3f5 !important;
        border-radius: 10px !important;
        padding: 12px 28px !important;
        border: 1px solid #dcdcdc !important;
        margin-right: 12px !important;
        transition: all 0.3s ease-in-out !important;
    }

    /* Sekme İçindeki Yazı ve İkonlar */
    .stTabs [data-baseweb="tab"] p {
        font-size: 18px !important;
        font-weight: 800 !important;
        color: #495057 !important;
        letter-spacing: 0.5px !important;
    }

    /* Hover (Üzerine Gelince) */
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #fff0f0 !important;
        border-color: #b22222 !important;
    }
    .stTabs [data-baseweb="tab"]:hover p {
        color: #b22222 !important;
    }

    /* Aktif (Seçili) Sekme */
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-bottom: 4px solid #b22222 !important; /* Sadece alt çizgi */
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.08) !important;
    }

    .stTabs [aria-selected="true"] p {
        color: #b22222 !important;
        font-weight: 900 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SVG LOGO HTML BİLEŞENİ
# ---------------------------------------------------------
LOGO_HTML = """
<div class="logo-container">
    <svg class="budget-logo-svg" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="8" y="14" width="48" height="40" rx="8" fill="#B22222" />
        <path d="M16 26H48" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>
        <rect x="14" y="32" width="8" height="14" rx="2" fill="#F7D070"/>
        <rect x="28" y="28" width="8" height="18" rx="2" fill="#FFFFFF"/>
        <rect x="42" y="22" width="8" height="24" rx="2" fill="#4CAF50"/>
        <circle cx="48" cy="14" r="7" fill="#F7D070" stroke="#FFFFFF" stroke-width="2"/>
        <text x="48" y="17.5" font-family="Arial" font-size="9" font-weight="bold" fill="#B22222" text-anchor="middle">₺</text>
    </svg>
</div>
"""

# ---------------------------------------------------------
# GİRİŞ / ŞİFRE KONTROLÜ (AUTHENTICATION)
# ---------------------------------------------------------
# AUTHENTICATION (KULLANICI ADI & ŞİFRE KONTROLÜ)
def check_password():
    def password_entered():
        user = st.session_state.get("username_input", "").strip()
        pwd = st.session_state.get("password_input", "")

        # secrets.toml dosyası varsa oradan okur, yoksa boş/geçersiz kalır
        try:
            allowed_users = st.secrets["passwords"]
        except Exception:
            # secrets.toml tanımlı değilse kimsenin girmesine izin verme
            allowed_users = {}

        if user in allowed_users and allowed_users[user] == pwd:
            st.session_state.authenticated = True
            st.session_state.user_role = user
            st.session_state.password_input = ""
            st.session_state.username_input = ""
        else:
            st.session_state.authenticated = False

    if st.session_state.get("authenticated", False):
        return True

    # Giriş Ekranı (Mevcut Tasarım Yapınız)
    st.markdown(LOGO_HTML, unsafe_allow_html=True)
    st.markdown("""
        <div class="main-title-container">
            <div class="main-title">POL.Bütçe</div>
            <div class="main-title-divider"></div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔒 Güvenli Giriş")
        st.text_input("Kullanıcı Adı", key="username_input")
        st.text_input("Şifrenizi Girin", type="password", key="password_input")
        st.button("Giriş Yap", type="primary", on_click=password_entered, use_container_width=True)
        
        if "authenticated" in st.session_state and not st.session_state.authenticated:
            st.error("🔑 Kullanıcı adı veya şifre hatalı!")

    return False

# Giriş yapılmadıysa uygulamanın kalanını çalıştırma!
if not check_password():
    st.stop()

# ---------------------------------------------------------
# UYGULAMA İÇERİĞİ (Giriş Yapıldıktan Sonra)
# ---------------------------------------------------------

with st.sidebar:
    st.write("👤 **Oturum Açıldı**")
    if st.button("🚪 Çıkış Yap", type="secondary"):
        logout()

MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# Helper Functions
def format_tl(val):
    if pd.isna(val) or val is None:
        val = 0.0
    return f"{val:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")

def format_ratio(val):
    if pd.isna(val) or val is None:
        return "%0,00"
    return f"%{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_color_style(val):
    if val < 0:
        return "color: #d9534f; font-weight: bold;"
    elif val > 0:
        return "color: #0275d8; font-weight: bold;"
    else:
        return "color: #333333; font-weight: bold;"

def fix_tr(text):
    if not isinstance(text, str):
        text = str(text)
    tr_map = {'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'}
    for tr, en in tr_map.items():
        text = text.replace(tr, en)
    return text

# Database Setup
DB_FILE = "budget.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, month)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS budget_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            budget_id INTEGER,
            item_type TEXT,
            category_name TEXT,
            estimated REAL,
            actual REAL,
            FOREIGN KEY (budget_id) REFERENCES budgets (id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS defined_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT,
            name TEXT UNIQUE
        )
    """)
    
    c.execute("SELECT COUNT(*) FROM defined_categories")
    if c.fetchone()[0] == 0:
        defaults = [
            ('GİDER', 'Kredi Kartı'), ('GİDER', 'Kira Ödemesi'), ('GİDER', 'İgdaş - Doğalgaz'), ('GİDER', 'İSKİ - Su'),
            ('GELİR', 'Maaş'), ('GELİR', 'Önceki Aydan Kalan')
        ]
        c.executemany("INSERT INTO defined_categories (item_type, name) VALUES (?, ?)", defaults)
        
    conn.commit()
    conn.close()

init_db()

# DB Queries
def get_all_budgets():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM budgets", conn)
    conn.close()
    if not df.empty:
        df['month_num'] = df['month'].apply(lambda x: MONTHS.index(x) + 1 if x in MONTHS else 1)
        df = df.sort_values(by=['year', 'month_num', 'id'], ascending=[False, False, False]).drop(columns=['month_num'])
    return df

def get_budget_items(budget_id):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM budget_items WHERE budget_id = ?", conn, params=(budget_id,))
    conn.close()
    return df

def get_all_budget_details():
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT b.id as budget_id, b.year, b.month, bi.item_type, bi.category_name, bi.estimated, bi.actual
        FROM budgets b
        JOIN budget_items bi ON b.id = bi.budget_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df['month_num'] = df['month'].apply(lambda x: MONTHS.index(x) + 1 if x in MONTHS else 1)
        df = df.sort_values(by=['year', 'month_num'])
    return df

def get_defined_categories(item_type):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT name FROM defined_categories WHERE item_type = ? ORDER BY id ASC", conn, params=(item_type,))
    conn.close()
    return df['name'].tolist()

def save_defined_category(item_type, name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO defined_categories (item_type, name) VALUES (?, ?)", (item_type, name.strip()))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

    upload_db_to_drive()

def delete_defined_category(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM defined_categories WHERE name = ?", (name,))
    conn.commit()
    conn.close()

    upload_db_to_drive()

def save_budget(year, month, expense_items, income_items, budget_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if budget_id is None:
        c.execute("INSERT OR REPLACE INTO budgets (year, month) VALUES (?, ?)", (year, month))
        budget_id = c.lastrowid
    else:
        c.execute("DELETE FROM budget_items WHERE budget_id = ?", (budget_id,))
    
    for item in expense_items:
        if item['name'].strip():
            c.execute("""
                INSERT INTO budget_items (budget_id, item_type, category_name, estimated, actual)
                VALUES (?, 'GİDER', ?, ?, ?)
            """, (budget_id, item['name'], float(item['estimated']), float(item['actual'])))
            
    for item in income_items:
        if item['name'].strip():
            c.execute("""
                INSERT INTO budget_items (budget_id, item_type, category_name, estimated, actual)
                VALUES (?, 'GELİR', ?, ?, ?)
            """, (budget_id, item['name'], float(item['estimated']), float(item['actual'])))
            
    conn.commit()
    conn.close()

    upload_db_to_drive()

def delete_budget(budget_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
    c.execute("DELETE FROM budget_items WHERE budget_id = ?", (budget_id,))
    conn.commit()
    conn.close()

    # Veri silindiği için Drive'a güncel halini yüklüyoruz:
    upload_db_to_drive()

# PDF Generator (Tekil Bütçe)
def generate_pdf(year, month, items_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    title_text = fix_tr(f"POL.BUTCE - {month.upper()} {year} RAPORU")
    pdf.cell(0, 10, title_text, ln=True, align="C")
    pdf.ln(5)
    
    exp_df = items_df[items_df['item_type'] == 'GİDER']
    inc_df = items_df[items_df['item_type'] == 'GELİR']
    
    pdf.set_font("Arial", "B", 12)
    
    # GİDER
    pdf.cell(0, 8, "GIDER BUTCESI", ln=True)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(50, 7, "Butce Adi", 1)
    pdf.cell(35, 7, "Tahmini", 1, 0, 'R')
    pdf.cell(35, 7, "Gerceklestirilen", 1, 0, 'R')
    pdf.cell(35, 7, "Fark", 1, 0, 'R')
    pdf.cell(35, 7, "Gerc. Orani", 1, 1, 'R')
    
    pdf.set_font("Arial", "", 9)
    tot_exp_est, tot_exp_act = 0.0, 0.0
    for _, r in exp_df.iterrows():
        diff = r['estimated'] - r['actual']
        ratio = (r['actual'] / r['estimated'] * 100) if r['estimated'] > 0 else 0
        tot_exp_est += r['estimated']
        tot_exp_act += r['actual']
        pdf.cell(50, 6, fix_tr(r['category_name']), 1)
        pdf.cell(35, 6, fix_tr(format_tl(r['estimated'])), 1, 0, 'R')
        pdf.cell(35, 6, fix_tr(format_tl(r['actual'])), 1, 0, 'R')
        pdf.cell(35, 6, fix_tr(format_tl(diff)), 1, 0, 'R')
        pdf.cell(35, 6, fix_tr(format_ratio(ratio)), 1, 1, 'R')
        
    tot_exp_diff = tot_exp_est - tot_exp_act
    tot_exp_ratio = (tot_exp_act / tot_exp_est * 100) if tot_exp_est > 0 else 0
    pdf.set_font("Arial", "B", 9)
    pdf.cell(50, 7, "TOPLAM GIDER", 1)
    pdf.cell(35, 7, fix_tr(format_tl(tot_exp_est)), 1, 0, 'R')
    pdf.cell(35, 7, fix_tr(format_tl(tot_exp_act)), 1, 0, 'R')
    pdf.cell(35, 7, fix_tr(format_tl(tot_exp_diff)), 1, 0, 'R')
    pdf.cell(35, 7, fix_tr(format_ratio(tot_exp_ratio)), 1, 1, 'R')
    
    pdf.ln(5)
    
    # GELİR
    pdf.cell(0, 8, "GELIR BUTCESI", ln=True)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(50, 7, "Butce Adi", 1)
    pdf.cell(35, 7, "Tahmini", 1, 0, 'R')
    pdf.cell(35, 7, "Gerceklestirilen", 1, 0, 'R')
    pdf.cell(35, 7, "Fark", 1, 0, 'R')
    pdf.cell(35, 7, "Gerc. Orani", 1, 1, 'R')
    
    pdf.set_font("Arial", "", 9)
    tot_inc_est, tot_inc_act = 0.0, 0.0
    for _, r in inc_df.iterrows():
        diff = r['actual'] - r['estimated']
        ratio = (r['actual'] / r['estimated'] * 100) if r['estimated'] > 0 else 0
        tot_inc_est += r['estimated']
        tot_inc_act += r['actual']
        pdf.cell(50, 6, fix_tr(r['category_name']), 1)
        pdf.cell(35, 6, fix_tr(format_tl(r['estimated'])), 1, 0, 'R')
        pdf.cell(35, 6, fix_tr(format_tl(r['actual'])), 1, 0, 'R')
        pdf.cell(35, 6, fix_tr(format_tl(diff)), 1, 0, 'R')
        pdf.cell(35, 6, fix_tr(format_ratio(ratio)), 1, 1, 'R')
        
    tot_inc_diff = tot_inc_act - tot_inc_est
    tot_inc_ratio = (tot_inc_act / tot_inc_est * 100) if tot_inc_est > 0 else 0
    pdf.set_font("Arial", "B", 9)
    pdf.cell(50, 7, "TOPLAM GELIR", 1)
    pdf.cell(35, 7, fix_tr(format_tl(tot_inc_est)), 1, 0, 'R')
    pdf.cell(35, 7, fix_tr(format_tl(tot_inc_act)), 1, 0, 'R')
    pdf.cell(35, 7, fix_tr(format_tl(tot_inc_diff)), 1, 0, 'R')
    pdf.cell(35, 7, fix_tr(format_ratio(tot_inc_ratio)), 1, 1, 'R')
    
    pdf.ln(5)
    
    # NET KALAN
    pdf.set_font("Arial", "B", 10)
    pdf.cell(70, 8, "NET KALAN (GELIR - GIDER)", 1)
    pdf.cell(60, 8, fix_tr(f"Tahmini: {format_tl(tot_inc_est - tot_exp_est)}"), 1, 0, 'R')
    pdf.cell(60, 8, fix_tr(f"Gerceklesen: {format_tl(tot_inc_act - tot_exp_act)}"), 1, 1, 'R')

    pdf_out = pdf.output()
    if isinstance(pdf_out, str):
        return pdf_out.encode('latin1')
    return bytes(pdf_out)

# PDF Generator (Analiz Filtre Raporu)
def generate_analysis_pdf(year, view_type, month, category, df_filtered):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    title_text = f"POL.BUTCE - ANALIZ VE OZET RAPORU ({year})"
    if month:
        title_text += f" - {month.upper()}"
    pdf.cell(0, 10, fix_tr(title_text), ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, fix_tr(f"Gorunum Turu: {view_type} | Kalem Filtresi: {category}"), ln=True, align="C")
    pdf.ln(6)

    # ÖZET METRİKLER
    tot_inc_act = df_filtered[df_filtered['item_type'] == 'GELİR']['actual'].sum()
    tot_exp_act = df_filtered[df_filtered['item_type'] == 'GİDER']['actual'].sum()
    tot_net_act = tot_inc_act - tot_exp_act

    tot_inc_est = df_filtered[df_filtered['item_type'] == 'GELİR']['estimated'].sum()
    tot_exp_est = df_filtered[df_filtered['item_type'] == 'GİDER']['estimated'].sum()
    tot_net_est = tot_inc_est - tot_exp_est

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "GENEL OZET METRIKLERI", ln=True)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(60, 7, "Metrik", 1)
    pdf.cell(65, 7, "Tahmini Tutar", 1, 0, 'R')
    pdf.cell(65, 7, "Gerceklesen Tutar", 1, 1, 'R')

    pdf.set_font("Arial", "", 9)
    pdf.cell(60, 6, "Toplam Gelir", 1)
    pdf.cell(65, 6, fix_tr(format_tl(tot_inc_est)), 1, 0, 'R')
    pdf.cell(65, 6, fix_tr(format_tl(tot_inc_act)), 1, 1, 'R')

    pdf.cell(60, 6, "Toplam Gider", 1)
    pdf.cell(65, 6, fix_tr(format_tl(tot_exp_est)), 1, 0, 'R')
    pdf.cell(65, 6, fix_tr(format_tl(tot_exp_act)), 1, 1, 'R')

    pdf.set_font("Arial", "B", 9)
    pdf.cell(60, 7, "NET KALAN / TASARRUF", 1)
    pdf.cell(65, 7, fix_tr(format_tl(tot_net_est)), 1, 0, 'R')
    pdf.cell(65, 7, fix_tr(format_tl(tot_net_act)), 1, 1, 'R')

    pdf.ln(8)

    # DETAY TABLOSU
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "FILTRELENMIS KALEM DETAYLARI", ln=True)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(22, 7, "Ay", 1)
    pdf.cell(20, 7, "Tur", 1)
    pdf.cell(58, 7, "Kategori / Kalem", 1)
    pdf.cell(30, 7, "Tahmini", 1, 0, 'R')
    pdf.cell(30, 7, "Gerceklese", 1, 0, 'R')
    pdf.cell(30, 7, "Fark", 1, 1, 'R')

    pdf.set_font("Arial", "", 8)
    for _, r in df_filtered.iterrows():
        diff = (r['estimated'] - r['actual']) if r['item_type'] == 'GİDER' else (r['actual'] - r['estimated'])
        pdf.cell(22, 6, fix_tr(r['month']), 1)
        pdf.cell(20, 6, fix_tr(r['item_type']), 1)
        pdf.cell(58, 6, fix_tr(r['category_name'][:30]), 1)
        pdf.cell(30, 6, fix_tr(format_tl(r['estimated'])), 1, 0, 'R')
        pdf.cell(30, 6, fix_tr(format_tl(r['actual'])), 1, 0, 'R')
        pdf.cell(30, 6, fix_tr(format_tl(diff)), 1, 1, 'R')

    pdf_out = pdf.output()
    return bytes(pdf_out) if isinstance(pdf_out, (str, bytearray)) else pdf_out

# POP-UP OPEN HELPER
def open_budget_modal(year, month, budget_id=None):
    st.session_state.show_modal = True
    st.session_state.modal_year = year
    st.session_state.modal_month = month
    st.session_state.modal_budget_id = budget_id
    
    def_expenses = get_defined_categories('GİDER')
    def_incomes = get_defined_categories('GELİR')

    if budget_id:
        existing_items = get_budget_items(budget_id)
        exp_df = existing_items[existing_items['item_type'] == 'GİDER']
        inc_df = existing_items[existing_items['item_type'] == 'GELİR']
        
        st.session_state.modal_exp_rows = [{"name": r['category_name'], "estimated": r['estimated'], "actual": r['actual']} for _, r in exp_df.iterrows()]
        st.session_state.modal_inc_rows = [{"name": r['category_name'], "estimated": r['estimated'], "actual": r['actual']} for _, r in inc_df.iterrows()]
    else:
        st.session_state.modal_exp_rows = [{"name": cat, "estimated": 0.0, "actual": 0.0} for cat in def_expenses]
        st.session_state.modal_inc_rows = [{"name": cat, "estimated": 0.0, "actual": 0.0} for cat in def_incomes]

# APP HEADER (LOGO + TITLE)
st.markdown(LOGO_HTML, unsafe_allow_html=True)
st.markdown("""
    <div class="main-title-container">
        <div class="main-title">POL.Bütçe</div>
        <div class="main-title-divider"></div>
    </div>
""", unsafe_allow_html=True)

# POP-UP MODAL RENDERING
if st.session_state.get("show_modal", False):
    year = st.session_state.modal_year
    month = st.session_state.modal_month
    budget_id = st.session_state.modal_budget_id

    st.markdown("---")
    st.markdown(f"### 📋 {month} {year} Bütçe Girişi / Düzenleme")

    # --- GİDER BÜTÇESİ ---
    st.markdown('<div class="section-header">GİDER BÜTÇESİ</div>', unsafe_allow_html=True)
    
    h1, h2, h3, h4, h5, _ = st.columns([3, 2, 2, 2, 2, 1])
    h1.caption("**Bütçe Adı**")
    h2.caption("**Tahmini Bütçe**")
    h3.caption("**Gerçekleşme**")
    h4.caption("**Fark**")
    h5.caption("**Gerç. Oranı**")

    tot_exp_est, tot_exp_act = 0.0, 0.0
    exp_to_delete = None

    for idx, item in enumerate(st.session_state.modal_exp_rows):
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 2, 1])
        
        item_name = c1.text_input(f"g_name_{idx}", value=item["name"], key=f"m_exp_name_{idx}", label_visibility="collapsed")
        est_val = c2.number_input(f"g_est_{idx}", value=float(item["estimated"]), step=500.0, key=f"m_exp_est_{idx}", label_visibility="collapsed")
        act_val = c3.number_input(f"g_act_{idx}", value=float(item["actual"]), step=500.0, key=f"m_exp_act_{idx}", label_visibility="collapsed")
        
        st.session_state.modal_exp_rows[idx]["name"] = item_name
        st.session_state.modal_exp_rows[idx]["estimated"] = est_val
        st.session_state.modal_exp_rows[idx]["actual"] = act_val

        diff = est_val - act_val
        ratio = (act_val / est_val * 100) if est_val > 0 else 0.0

        tot_exp_est += est_val
        tot_exp_act += act_val

        color_style = get_color_style(diff)
        c4.markdown(f"<div style='text-align:right; {color_style}'>{format_tl(diff)}</div>", unsafe_allow_html=True)
        c5.markdown(f"<div style='text-align:right; {color_style}'>{format_ratio(ratio)}</div>", unsafe_allow_html=True)

        if c6.button("🗑️", key=f"m_del_exp_{idx}"):
            exp_to_delete = idx

    if exp_to_delete is not None:
        st.session_state.modal_exp_rows.pop(exp_to_delete)
        st.rerun()

    tot_exp_diff = tot_exp_est - tot_exp_act
    tot_exp_ratio = (tot_exp_act / tot_exp_est * 100) if tot_exp_est > 0 else 0.0
    
    st.markdown("---")
    tc1, tc2, tc3, tc4, tc5, _ = st.columns([3, 2, 2, 2, 2, 1])
    tc1.markdown("**TOPLAM GİDER**")
    tc2.markdown(f"<div style='text-align:right;'><b>{format_tl(tot_exp_est)}</b></div>", unsafe_allow_html=True)
    tc3.markdown(f"<div style='text-align:right;'><b>{format_tl(tot_exp_act)}</b></div>", unsafe_allow_html=True)
    tc4.markdown(f"<div style='text-align:right; {get_color_style(tot_exp_diff)}'>{format_tl(tot_exp_diff)}</div>", unsafe_allow_html=True)
    tc5.markdown(f"<div style='text-align:right; {get_color_style(tot_exp_diff)}'>{format_ratio(tot_exp_ratio)}</div>", unsafe_allow_html=True)

    if st.button("➕ Gider Satırı Ekle", key="m_add_exp_btn"):
        st.session_state.modal_exp_rows.append({"name": "", "estimated": 0.0, "actual": 0.0})
        st.rerun()

    # --- GELİR BÜTÇESİ ---
    st.markdown('<div class="section-header">GELİR BÜTÇESİ</div>', unsafe_allow_html=True)
    
    h1, h2, h3, h4, h5, _ = st.columns([3, 2, 2, 2, 2, 1])
    h1.caption("**Bütçe Adı**")
    h2.caption("**Tahmini Bütçe**")
    h3.caption("**Gerçekleşme**")
    h4.caption("**Fark**")
    h5.caption("**Gerç. Oranı**")

    tot_inc_est, tot_inc_act = 0.0, 0.0
    inc_to_delete = None

    for idx, item in enumerate(st.session_state.modal_inc_rows):
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 2, 1])
        
        item_name = c1.text_input(f"i_name_{idx}", value=item["name"], key=f"m_inc_name_{idx}", label_visibility="collapsed")
        est_val = c2.number_input(f"i_est_{idx}", value=float(item["estimated"]), step=500.0, key=f"m_inc_est_{idx}", label_visibility="collapsed")
        act_val = c3.number_input(f"i_act_{idx}", value=float(item["actual"]), step=500.0, key=f"m_inc_act_{idx}", label_visibility="collapsed")
        
        st.session_state.modal_inc_rows[idx]["name"] = item_name
        st.session_state.modal_inc_rows[idx]["estimated"] = est_val
        st.session_state.modal_inc_rows[idx]["actual"] = act_val

        diff = act_val - est_val
        ratio = (act_val / est_val * 100) if est_val > 0 else 0.0

        tot_inc_est += est_val
        tot_inc_act += act_val

        color_style = get_color_style(diff)
        c4.markdown(f"<div style='text-align:right; {color_style}'>{format_tl(diff)}</div>", unsafe_allow_html=True)
        c5.markdown(f"<div style='text-align:right; {color_style}'>{format_ratio(ratio)}</div>", unsafe_allow_html=True)

        if c6.button("🗑️", key=f"m_del_inc_{idx}"):
            inc_to_delete = idx

    if inc_to_delete is not None:
        st.session_state.modal_inc_rows.pop(inc_to_delete)
        st.rerun()

    tot_inc_diff = tot_inc_act - tot_inc_est
    tot_inc_ratio = (tot_inc_act / tot_inc_est * 100) if tot_inc_est > 0 else 0.0

    st.markdown("---")
    ic1, ic2, ic3, ic4, ic5, _ = st.columns([3, 2, 2, 2, 2, 1])
    ic1.markdown("**TOPLAM GELİR**")
    ic2.markdown(f"<div style='text-align:right;'><b>{format_tl(tot_inc_est)}</b></div>", unsafe_allow_html=True)
    ic3.markdown(f"<div style='text-align:right;'><b>{format_tl(tot_inc_act)}</b></div>", unsafe_allow_html=True)
    ic4.markdown(f"<div style='text-align:right; {get_color_style(tot_inc_diff)}'>{format_tl(tot_inc_diff)}</div>", unsafe_allow_html=True)
    ic5.markdown(f"<div style='text-align:right; {get_color_style(tot_inc_diff)}'>{format_ratio(tot_inc_ratio)}</div>", unsafe_allow_html=True)

    if st.button("➕ Gelir Satırı Ekle", key="m_add_inc_btn"):
        st.session_state.modal_inc_rows.append({"name": "", "estimated": 0.0, "actual": 0.0})
        st.rerun()

    rem_est = tot_inc_est - tot_exp_est
    rem_act = tot_inc_act - tot_exp_act

    st.markdown('<div class="section-header" style="background-color:#f4a261; color:white;">NET KALAN BÜTÇE ÖZETİ</div>', unsafe_allow_html=True)
    kc1, kc2, kc3 = st.columns([4, 3, 3])
    kc1.markdown("**NET KALAN**")
    
    style_est = get_color_style(rem_est)
    style_act = get_color_style(rem_act)
    
    kc2.markdown(f"**Tahmini:** <span style='{style_est}'>{format_tl(rem_est)}</span>", unsafe_allow_html=True)
    kc3.markdown(f"**Gerçekleşen:** <span style='{style_act}'>{format_tl(rem_act)}</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    btn_save, btn_cancel, _ = st.columns([2, 2, 6])
    
    if btn_save.button("💾 KAYDET VE KAPAT", type="primary"):
        save_budget(year, month, st.session_state.modal_exp_rows, st.session_state.modal_inc_rows, budget_id)
        st.session_state.show_modal = False
        st.success("Bütçe kaydedildi!")
        st.rerun()

    if btn_cancel.button("❌ İPTAL"):
        st.session_state.show_modal = False
        st.rerun()

    st.markdown("---")

# TABS
tab_budget, tab_analysis, tab_settings = st.tabs(["📊 BÜTÇE", "📈 ANALİZ", "⚙️ KALEM TANIMLARI"])

with tab_budget:
    col_y, col_m, col_btn = st.columns([3, 3, 2])
    
    current_year = datetime.now().year
    years = list(range(current_year - 2, current_year + 5))
    
    with col_y:
        selected_year = st.selectbox("Yıl Seçin", years, index=years.index(current_year))
    with col_m:
        selected_month = st.selectbox("Ay Seçin", MONTHS, index=datetime.now().month - 1)
    with col_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("➕ EKLE", type="primary"):
            open_budget_modal(selected_year, selected_month)
            st.rerun()

    st.markdown("---")
    st.subheader("📚 Kayıtlı Bütçe Geçmişi")
    
    all_b = get_all_budgets()
    if all_b.empty:
        st.info("Henüz kaydedilmiş bütçe bulunmuyor. Üstteki 'EKLE' butonundan yeni bütçe oluşturabilirsiniz.")
    else:
        for _, row in all_b.iterrows():
            b_id = int(row['id'])
            b_year = row['year']
            b_month = row['month']
            
            items = get_budget_items(b_id)
            exp_df = items[items['item_type'] == 'GİDER'] if not items.empty else pd.DataFrame()
            inc_df = items[items['item_type'] == 'GELİR'] if not items.empty else pd.DataFrame()
            
            exp_sum = exp_df['actual'].sum() if not exp_df.empty else 0.0
            inc_sum = inc_df['actual'].sum() if not inc_df.empty else 0.0
            net_act = inc_sum - exp_sum
            
            net_color = get_color_style(net_act)
            
            with st.expander(f"🗓️ {b_month} {b_year} Bütçesi"):
                st.markdown(
                    f"**Toplam Gelir:** {format_tl(inc_sum)} | "
                    f"**Toplam Gider:** {format_tl(exp_sum)} | "
                    f"**Net Kalan:** <span style='{net_color}'>{format_tl(net_act)}</span>",
                    unsafe_allow_html=True
                )
                
                b_col1, b_col2, b_col3, _ = st.columns([2, 2, 2, 4])
                
                with b_col1:
                    show_detail = st.button("🔍 Detay", key=f"det_{b_id}")
                with b_col2:
                    if st.button("✏️ Düzenle", key=f"edit_{b_id}"):
                        open_budget_modal(b_year, b_month, b_id)
                        st.rerun()
                with b_col3:
                    if st.button("🗑️ Sil", key=f"del_{b_id}"):
                        delete_budget(b_id)
                        st.success("Bütçe silindi.")
                        st.rerun()

                if show_detail:
                    st.markdown("---")
                    col_config = {
                        "Bütçe Adı": st.column_config.TextColumn("Bütçe Adı"),
                        "Tahmini Bütçe": st.column_config.TextColumn("Tahmini Bütçe", alignment="right"),
                        "Gerçekleşme": st.column_config.TextColumn("Gerçekleşme", alignment="right"),
                        "Fark": st.column_config.TextColumn("Fark", alignment="right"),
                        "Gerçekleşme Oranı": st.column_config.TextColumn("Gerçekleşme Oranı", alignment="right")
                    }

                    def style_table(df_data):
                        styles = pd.DataFrame('', index=df_data.index, columns=df_data.columns)
                        for i, r in df_data.iterrows():
                            if r["Bütçe Adı"] == "TOPLAM":
                                for col in df_data.columns:
                                    styles.at[i, col] += " font-weight: bold; background-color: #f8f9fa;"
                            val_str = str(r["Fark"])
                            if "-" in val_str:
                                styles.at[i, "Fark"] += " color: #d9534f; font-weight: bold;"
                                styles.at[i, "Gerçekleşme Oranı"] += " color: #d9534f; font-weight: bold;"
                            elif val_str == "0,00 TL":
                                styles.at[i, "Fark"] += " color: #333333;"
                                styles.at[i, "Gerçekleşme Oranı"] += " color: #333333;"
                            else:
                                styles.at[i, "Fark"] += " color: #0275d8; font-weight: bold;"
                                styles.at[i, "Gerçekleşme Oranı"] += " color: #0275d8; font-weight: bold;"
                        return styles

                    st.markdown("**GİDER BÜTÇESİ**")
                    tot_exp_est, tot_exp_act = 0.0, 0.0
                    exp_data = []
                    if not exp_df.empty:
                        for _, r in exp_df.iterrows():
                            diff = r['estimated'] - r['actual']
                            ratio = (r['actual'] / r['estimated'] * 100) if r['estimated'] > 0 else 0
                            tot_exp_est += r['estimated']
                            tot_exp_act += r['actual']
                            exp_data.append({
                                "Bütçe Adı": r['category_name'],
                                "Tahmini Bütçe": format_tl(r['estimated']),
                                "Gerçekleşme": format_tl(r['actual']),
                                "Fark": format_tl(diff),
                                "Gerçekleşme Oranı": format_ratio(ratio)
                            })
                        
                        tot_exp_diff = tot_exp_est - tot_exp_act
                        tot_exp_ratio = (tot_exp_act / tot_exp_est * 100) if tot_exp_est > 0 else 0
                        exp_data.append({
                            "Bütçe Adı": "TOPLAM",
                            "Tahmini Bütçe": format_tl(tot_exp_est),
                            "Gerçekleşme": format_tl(tot_exp_act),
                            "Fark": format_tl(tot_exp_diff),
                            "Gerçekleşme Oranı": format_ratio(tot_exp_ratio)
                        })

                        df_exp_disp = pd.DataFrame(exp_data)
                        styled_exp = df_exp_disp.style.apply(style_table, axis=None)
                        st.dataframe(styled_exp, column_config=col_config, use_container_width=True, hide_index=True)
                    
                    st.markdown("**GELİR BÜTÇESİ**")
                    tot_inc_est, tot_inc_act = 0.0, 0.0
                    inc_data = []
                    if not inc_df.empty:
                        for _, r in inc_df.iterrows():
                            diff = r['actual'] - r['estimated']
                            ratio = (r['actual'] / r['estimated'] * 100) if r['estimated'] > 0 else 0
                            tot_inc_est += r['estimated']
                            tot_inc_act += r['actual']
                            inc_data.append({
                                "Bütçe Adı": r['category_name'],
                                "Tahmini Bütçe": format_tl(r['estimated']),
                                "Gerçekleşme": format_tl(r['actual']),
                                "Fark": format_tl(diff),
                                "Gerçekleşme Oranı": format_ratio(ratio)
                            })
                        
                        tot_inc_diff = tot_inc_act - tot_inc_est
                        tot_inc_ratio = (tot_inc_act / tot_inc_est * 100) if tot_inc_est > 0 else 0
                        inc_data.append({
                            "Bütçe Adı": "TOPLAM",
                            "Tahmini Bütçe": format_tl(tot_inc_est),
                            "Gerçekleşme": format_tl(tot_inc_act),
                            "Fark": format_tl(tot_inc_diff),
                            "Gerçekleşme Oranı": format_ratio(tot_inc_ratio)
                        })

                        df_inc_disp = pd.DataFrame(inc_data)
                        styled_inc = df_inc_disp.style.apply(style_table, axis=None)
                        st.dataframe(styled_inc, column_config=col_config, use_container_width=True, hide_index=True)

                    det_rem_est = tot_inc_est - tot_exp_est
                    det_rem_act = tot_inc_act - tot_exp_act
                    
                    st.markdown("""
                        <div class="section-header" style="background-color:#f4a261; color:white;">
                            NET KALAN BÜTÇE ÖZETİ
                        </div>
                    """, unsafe_allow_html=True)
                    
                    d_kc1, d_kc2, d_kc3 = st.columns([4, 3, 3])
                    d_kc1.markdown("**GELİR - GİDER KALAN**")
                    
                    c_est = get_color_style(det_rem_est)
                    c_act = get_color_style(det_rem_act)
                    
                    d_kc2.markdown(f"**Tahmini Kalan:** <span style='{c_est}'>{format_tl(det_rem_est)}</span>", unsafe_allow_html=True)
                    d_kc3.markdown(f"**Gerçekleşen Kalan:** <span style='{c_act}'>{format_tl(det_rem_act)}</span>", unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)

                    pdf_bytes = generate_pdf(b_year, b_month, items)
                    st.download_button(
                        label="📄 RAPOR (PDF İndir)",
                        data=pdf_bytes,
                        file_name=f"POL_Butce_{b_month}_{b_year}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{b_id}"
                    )

# --- ANALİZ SEKMESİ ---
with tab_analysis:
    st.subheader("📈 Dinamik Bütçe Analizi ve Görselleştirme")
    
    df_all = get_all_budget_details()
    
    if df_all.empty:
        st.info("Analiz yapılabilecek herhangi bir bütçe verisi bulunamadı. Lütfen öncelikle bütçe kaydı ekleyin.")
    else:
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        
        view_type = f_col1.selectbox("Görünüm Türü", ["Yıllık Genel Bakış", "Aylık Detay Bakış"])
        
        available_years = sorted(df_all['year'].unique().tolist(), reverse=True)
        selected_an_year = f_col2.selectbox("Analiz Yılı", available_years)
        
        if view_type == "Aylık Detay Bakış":
            available_months = df_all[df_all['year'] == selected_an_year]['month'].unique().tolist()
            available_months = sorted(available_months, key=lambda x: MONTHS.index(x) if x in MONTHS else 0)
            selected_an_month = f_col3.selectbox("Analiz Ayı", available_months)
        else:
            selected_an_month = None
            f_col3.empty()
            
        all_categories = ["Tüm Kalemler"] + sorted(df_all['category_name'].unique().tolist())
        selected_category = f_col4.selectbox("Bütçe Kalemi Filtresi", all_categories)
        
        df_filtered = df_all[df_all['year'] == selected_an_year]
        if selected_an_month:
            df_filtered = df_filtered[df_filtered['month'] == selected_an_month]
        if selected_category != "Tüm Kalemler":
            df_filtered = df_filtered[df_filtered['category_name'] == selected_category]

        analysis_pdf_bytes = generate_analysis_pdf(
            selected_an_year, view_type, selected_an_month, selected_category, df_filtered
        )
        st.download_button(
            label="📄 Filtrelenmiş Analiz Raporunu İndir (PDF)",
            data=analysis_pdf_bytes,
            file_name=f"POL_Butce_Analiz_{selected_an_year}.pdf",
            mime="application/pdf",
            type="primary"
        )
            
        st.markdown("---")
        
        tot_inc_actual = df_filtered[df_filtered['item_type'] == 'GELİR']['actual'].sum()
        tot_exp_actual = df_filtered[df_filtered['item_type'] == 'GİDER']['actual'].sum()
        tot_net_actual = tot_inc_actual - tot_exp_actual
        
        tot_inc_est = df_filtered[df_filtered['item_type'] == 'GELİR']['estimated'].sum()
        tot_exp_est = df_filtered[df_filtered['item_type'] == 'GİDER']['estimated'].sum()
        tot_net_est = tot_inc_est - tot_exp_est

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Toplam Gelir (Gerçekleşen)", format_tl(tot_inc_actual), delta=f"Tahmin: {format_tl(tot_inc_est)}")
        with m2:
            st.metric("Toplam Gider (Gerçekleşen)", format_tl(tot_exp_actual), delta=f"Tahmin: {format_tl(tot_exp_est)}", delta_color="inverse")
        with m3:
            st.metric("Net Kalan / Tasarruf", format_tl(tot_net_actual), delta=f"Tahmin: {format_tl(tot_net_est)}")

        st.markdown("<br>", unsafe_allow_html=True)

        if view_type == "Yıllık Genel Bakış":
            st.markdown(f"### 📊 {selected_an_year} Yılı Aylık Toplamlar")
            
            metric_view = st.radio(
                "Gösterilecek Metrik:", 
                ["Gelir & Gider Karşılaştırma", "Sadece Gelir Toplamları", "Sadece Gider Toplamları"], 
                horizontal=True
            )

            monthly_summary = df_filtered.groupby(['month', 'month_num', 'item_type'])['actual'].sum().reset_index()
            monthly_summary = monthly_summary.sort_values('month_num')
            
            pivot_m = monthly_summary.pivot(index='month', columns='item_type', values='actual').fillna(0)
            
            present_months = [m for m in MONTHS if m in pivot_m.index]
            pivot_m = pivot_m.reindex(present_months)
            
            if 'GELİR' not in pivot_m.columns: pivot_m['GELİR'] = 0.0
            if 'GİDER' not in pivot_m.columns: pivot_m['GİDER'] = 0.0
            pivot_m['NET KALAN'] = pivot_m['GELİR'] - pivot_m['GİDER']
            
            fig_bar_monthly = go.Figure()

            if metric_view == "Sadece Gelir Toplamları":
                fig_bar_monthly.add_trace(go.Bar(
                    x=pivot_m.index, 
                    y=pivot_m['GELİR'], 
                    name='Gelir', 
                    marker_color='#1f77b4',
                    text=[format_tl(v) for v in pivot_m['GELİR']],
                    textposition='auto'
                ))
            elif metric_view == "Sadece Gider Toplamları":
                fig_bar_monthly.add_trace(go.Bar(
                    x=pivot_m.index, 
                    y=pivot_m['GİDER'], 
                    name='Gider', 
                    marker_color='#d62728',
                    text=[format_tl(v) for v in pivot_m['GİDER']],
                    textposition='auto'
                ))
            else:
                fig_bar_monthly.add_trace(go.Bar(
                    x=pivot_m.index, 
                    y=pivot_m['GELİR'], 
                    name='Gelir', 
                    marker_color='#1f77b4'
                ))
                fig_bar_monthly.add_trace(go.Bar(
                    x=pivot_m.index, 
                    y=pivot_m['GİDER'], 
                    name='Gider', 
                    marker_color='#d62728'
                ))
                fig_bar_monthly.add_trace(go.Scatter(
                    x=pivot_m.index, 
                    y=pivot_m['NET KALAN'], 
                    name='Net Kalan', 
                    line=dict(color='#ff7f0e', width=3, dash='dot')
                ))

            fig_bar_monthly.update_layout(
                barmode='group', 
                hovermode="x unified", 
                height=400, 
                xaxis_title="Ay",
                yaxis_title="Tutar (TL)",
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_bar_monthly, use_container_width=True)

        g_col1, g_col2 = st.columns(2)
        
        with g_col1:
            st.markdown("### 🍕 Gider Kalemleri Dağılımı")
            exp_filtered = df_filtered[df_filtered['item_type'] == 'GİDER']
            if exp_filtered.empty or exp_filtered['actual'].sum() == 0:
                st.info("Gösterilecek gider verisi bulunamadı.")
            else:
                cat_exp_summary = exp_filtered.groupby('category_name')['actual'].sum().reset_index()
                fig_pie = px.pie(
                    cat_exp_summary, 
                    values='actual', 
                    names='category_name', 
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_pie, use_container_width=True)

        with g_col2:
            st.markdown("### 🎯 Tahmini vs Gerçekleşen Bütçe Kıyaslaması")
            if df_filtered.empty:
                st.info("Gösterilecek bütçe verisi bulunamadı.")
            else:
                item_summary = df_filtered.groupby('category_name')[['estimated', 'actual']].sum().reset_index()
                
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(x=item_summary['category_name'], y=item_summary['estimated'], name='Tahmini', marker_color='#ff7f0e'))
                fig_bar.add_trace(go.Bar(x=item_summary['category_name'], y=item_summary['actual'], name='Gerçekleşen', marker_color='#1f77b4'))
                
                fig_bar.update_layout(barmode='group', height=380, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_bar, use_container_width=True)

        if selected_category != "Tüm Kalemler":
            st.markdown(f"### 🔍 '{selected_category}' Kaleminin Zaman İçi Değişimi")
            cat_df = df_all[(df_all['year'] == selected_an_year) & (df_all['category_name'] == selected_category)]
            
            if not cat_df.empty:
                cat_df = cat_df.sort_values('month_num')
                fig_cat = px.line(
                    cat_df, 
                    x='month', 
                    y=['estimated', 'actual'], 
                    markers=True,
                    labels={'value': 'Tutar (TL)', 'variable': 'Tür', 'month': 'Ay'},
                    title=f"{selected_an_year} Yılı - {selected_category} Aylık Gelişimi"
                )
                fig_cat.update_layout(height=350)
                st.plotly_chart(fig_cat, use_container_width=True)

with tab_settings:
    st.subheader("⚙️ Sabit Bütçe Kalemleri Yönetimi")
    st.write("Sık kullandığınız Gelir ve Gider kalemlerini buraya ekleyin. Bütçe girerken pencerede otomatik olarak hazır geleceklerdir.")
    
    col_exp_mgr, col_inc_mgr = st.columns(2)
    
    with col_exp_mgr:
        st.markdown("**Gider Kalemleri Listesi**")
        exp_cats = get_defined_categories('GİDER')
        
        new_exp = st.text_input("Yeni Gider Kalemi Adı", key="new_exp_cat_input")
        if st.button("➕ Gider Kalemi Ekle", key="btn_add_exp_cat"):
            if new_exp.strip():
                save_defined_category('GİDER', new_exp)
                st.success(f"'{new_exp}' eklendi.")
                st.rerun()
                
        for c_name in exp_cats:
            c_col1, c_col2 = st.columns([4, 1])
            c_col1.write(f"• {c_name}")
            if c_col2.button("❌", key=f"del_exp_cat_{c_name}"):
                delete_defined_category(c_name)
                st.rerun()

    with col_inc_mgr:
        st.markdown("**Gelir Kalemleri Listesi**")
        inc_cats = get_defined_categories('GELİR')
        
        new_inc = st.text_input("Yeni Gelir Kalemi Adı", key="new_inc_cat_input")
        if st.button("➕ Gelir Kalemi Ekle", key="btn_add_inc_cat"):
            if new_inc.strip():
                save_defined_category('GELİR', new_inc)
                st.success(f"'{new_inc}' eklendi.")
                st.rerun()
                
        for c_name in inc_cats:
            c_col1, c_col2 = st.columns([4, 1])
            c_col1.write(f"• {c_name}")
            if c_col2.button("❌", key=f"del_inc_cat_{c_name}"):
                delete_defined_category(c_name)
                st.rerun()
