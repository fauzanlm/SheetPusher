import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import json
from cleaner import (
    clean_column_name,
    make_columns_unique,
    clean_dataframe,
    normalize_dataframe_headers
)

# Set Page Config
st.set_page_config(
    page_title="SheetPusher - Excel & CSV to DB ETL Tool",
    page_icon="🚀",
    layout="wide"
)

CONFIG_FILE = "db_config.json"

# Helper to load config
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

# Helper to save config
def save_config(config_data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f)

# Load existing config
saved_config = load_config()

st.title("🚀 SheetPusher: Excel & CSV to Database ETL")
st.markdown(
    "Automated data ingestion pipeline: upload raw spreadsheets, sanitize column headers into snake_case, "
    "clean empty records/whitespace, and load directly into your SQL database."
)

# Sidebar: Database Configuration
st.sidebar.header("🛠️ Database Configuration")
dialects = ["mariadb", "mysql", "postgresql", "sqlite", "mssql"]
default_dialect = saved_config.get("db_type", "mariadb")
dialect_index = dialects.index(default_dialect) if default_dialect in dialects else 0

db_type = st.sidebar.selectbox("Dialect", dialects, index=dialect_index)
db_host = st.sidebar.text_input("Host", value=saved_config.get("db_host", "localhost"))
db_port = st.sidebar.text_input(
    "Port",
    value=saved_config.get("db_port", "3306" if db_type in ["mysql", "mariadb"] else "5432")
)
db_user = st.sidebar.text_input("Username", value=saved_config.get("db_user", "root"))
db_pass = st.sidebar.text_input("Password", type="password", value=saved_config.get("db_pass", ""))
db_name = st.sidebar.text_input("Database Name", value=saved_config.get("db_name", "test_db"))

if st.sidebar.button("💾 Save Database Profile"):
    config_to_save = {
        "db_type": db_type,
        "db_host": db_host,
        "db_port": db_port,
        "db_user": db_user,
        "db_pass": db_pass,
        "db_name": db_name
    }
    save_config(config_to_save)
    st.sidebar.success("Database configuration saved locally!")

# Connection String Builder
def get_connection_url():
    if db_type == "sqlite":
        return f"sqlite:///{db_name}.db"
    elif db_type in ["mariadb", "mysql"]:
        return f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    elif db_type == "postgresql":
        return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    else:
        return None

# Main Area: File Upload
uploaded_file = st.file_uploader(
    "Upload your spreadsheet file",
    type=["xlsx", "xls", "csv"],
    help="Supports modern Excel (.xlsx), legacy Excel (.xls), and comma-separated values (.csv)."
)

if uploaded_file:
    original_filename = os.path.splitext(uploaded_file.name)[0]
    is_csv = uploaded_file.name.lower().endswith(".csv")

    # 1. Load File Data
    if is_csv:
        df = pd.read_csv(uploaded_file)
        selected_sheet = original_filename
        st.info(f"📄 Processing CSV file: `{uploaded_file.name}` ({len(df)} raw rows)")
    else:
        xl = pd.ExcelFile(uploaded_file)
        sheet_names = xl.sheet_names
        st.subheader("📄 Sheet Selection")
        selected_sheet = st.selectbox("Select Sheet to Process", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

    # --- DATA CLEANSING START ---
    df, stats = clean_dataframe(df)
    
    if stats["empty_rows_dropped"] > 0:
        st.warning(f"🧹 Cleansing: Removed {stats['empty_rows_dropped']} completely empty row(s).")
    if stats["empty_cols_dropped"] > 0:
        st.warning(f"🧹 Cleansing: Removed {stats['empty_cols_dropped']} completely empty column(s).")
    # --- DATA CLEANSING END ---

    # --- COLUMN SELECTION START ---
    st.subheader("🎯 Column Configuration")
    all_columns = df.columns.tolist()
    selected_columns = st.multiselect(
        "Select Columns to Import", 
        options=all_columns, 
        default=all_columns
    )
    
    if not selected_columns:
        st.error("⚠️ Please select at least one column to proceed.")
        st.stop()
        
    df = df[selected_columns]
    # --- COLUMN SELECTION END ---

    st.subheader("📋 Data Preview (Cleaned & Filtered)")
    st.dataframe(df.head(10))

    # 2. Table & Mode Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏗️ Table Naming")
        naming_option = st.radio("Choose Table Name Source:", ["Use File Name", "Use Sheet Name", "Custom Table Name"])
        if naming_option == "Use File Name":
            table_name = clean_column_name(original_filename)
        elif naming_option == "Use Sheet Name":
            table_name = clean_column_name(selected_sheet)
        else:
            custom_default = clean_column_name(selected_sheet) if selected_sheet else "imported_data"
            table_name = st.text_input("Enter Table Name", value=custom_default)
            table_name = clean_column_name(table_name)
        st.info(f"Target SQL Table: `{table_name}`")

    with col2:
        st.subheader("📥 Insert Mode")
        insert_mode = st.radio(
            "What to do if table exists?",
            ["Replace (Overwrite Table)", "Append (Add to Existing)"],
            help="'Replace' will drop the old table. 'Append' will keep existing data."
        )
        sql_mode = "replace" if "Replace" in insert_mode else "append"

    # 3. Transform Column Names (Handle Duplicates & Snake Case)
    df_transformed = normalize_dataframe_headers(df)
    
    st.subheader("✨ Transformed Schema Preview (Snake Case & Deduplicated Headers)")
    st.dataframe(df_transformed.head(10))
    
    # 4. Run ETL
    if st.button("🔥 Run ETL (Push to Database)"):
        with st.status("🚀 Processing ETL Pipeline...", expanded=True) as status:
            try:
                conn_url = get_connection_url()
                if not conn_url:
                    st.error(f"Dialect '{db_type}' is not currently configured for direct URI connection.")
                    status.update(label="❌ ETL Failed", state="error")
                else:
                    status.write("🔌 Connecting to Database Engine...")
                    engine = create_engine(conn_url)
                    
                    with engine.connect() as conn:
                        status.write("✅ Database Connected Successfully!")
                        status.write(f"📤 Pushing {len(df_transformed)} rows to table `{table_name}` using `{sql_mode}` mode...")
                        
                        # Chunked insertion for performance and stability
                        df_transformed.to_sql(table_name, con=engine, if_exists=sql_mode, index=False, chunksize=1000)
                        
                        status.update(label="🎊 ETL Successfully Completed!", state="complete", expanded=False)
                        st.balloons()
                        st.success(f"Successfully loaded {len(df_transformed)} records into table `{table_name}` ({sql_mode})!")
                        
            except Exception as e:
                st.error(f"❌ Error during ETL execution: {str(e)}")
                status.update(label="❌ ETL Failed", state="error")

else:
    st.info("👋 Upload an Excel (.xlsx, .xls) or CSV file above to begin data cleansing and database ingestion.")

st.markdown("---")
st.caption("SheetPusher • Lightweight Spreadsheet-to-Database ETL Pipeline • Built with Streamlit & Pandas")
