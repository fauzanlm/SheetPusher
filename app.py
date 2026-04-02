import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import re
import os
import json

# Set Page Config
st.set_page_config(page_title="Excel to DB ETL Tool", layout="wide")

CONFIG_FILE = "db_config.json"

# Helper to load config
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

# Helper to save config
def save_config(config_data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f)

# Load existing config
saved_config = load_config()

# Helper function to clean column names (lowercase + underscore)
def clean_column_name(column_name):
    # Strip spaces, convert to lowercase, replace non-alphanumeric with underscore
    clean_name = str(column_name).strip().lower()
    clean_name = re.sub(r'[^a-z0-9]', '_', clean_name)
    # Remove multiple underscores
    clean_name = re.sub(r'_+', '_', clean_name)
    return clean_name.strip('_')

# Function to handle duplicate column names
def make_columns_unique(columns):
    seen = {}
    new_cols = []
    for col in columns:
        base_name = clean_column_name(col)
        if not base_name: # Handle empty headers
            base_name = "unnamed_column"
            
        if base_name in seen:
            seen[base_name] += 1
            new_cols.append(f"{base_name}_duplicate{seen[base_name]}")
        else:
            seen[base_name] = 0
            new_cols.append(base_name)
    return new_cols

st.title("🚀 Python Excel to Database ETL")
st.markdown("Upload Excel, Convert Columns to Snake Case, and Push to Database.")

# Sidebar: Database Configuration
st.sidebar.header("🛠️ Database Configuration")
db_type = st.sidebar.selectbox("Dialect", ["mariadb", "mysql", "postgresql", "sqlite", "mssql"], 
                               index=["mariadb", "mysql", "postgresql", "sqlite", "mssql"].index(saved_config.get("db_type", "mariadb")))
db_host = st.sidebar.text_input("Host", value=saved_config.get("db_host", "localhost"))
db_port = st.sidebar.text_input("Port", value=saved_config.get("db_port", "3306" if db_type in ["mysql", "mariadb"] else "5432"))
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
    st.sidebar.success("Settings saved locally!")

# Connection String Builder
def get_connection_url():
    if db_type == "sqlite":
        return f"sqlite:///{db_name}.db"
    elif db_type == "mariadb":
        return f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    elif db_type == "mysql":
        return f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    elif db_type == "postgresql":
        return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    else:
        return None

# Main Area: File Upload
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

if uploaded_file:
    # 1. Load Excel File to get Sheet Names
    xl = pd.ExcelFile(uploaded_file)
    sheet_names = xl.sheet_names
    
    st.subheader("📄 Excel Configuration")
    selected_sheet = st.selectbox("Select Sheet to Process", sheet_names)
    
    # Load Data from Selected Sheet
    df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
    original_filename = os.path.splitext(uploaded_file.name)[0]
    
    # --- DATA CLEANSING START ---
    initial_rows = len(df)
    df.dropna(how='all', inplace=True)
    rows_after_dropna = len(df)
    df.dropna(axis=1, how='all', inplace=True)
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    df = df.where(pd.notnull(df), None)
    
    if initial_rows > rows_after_dropna:
        st.warning(f"🧹 Cleansing: Removed {initial_rows - rows_after_dropna} empty rows.")
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
    st.dataframe(df.head())

    # 2. Table & Mode Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏗️ Table Naming")
        naming_option = st.radio("Choose Table Name:", ["Use File Name", "Use Sheet Name", "Custom Table Name"])
        if naming_option == "Use File Name":
            table_name = clean_column_name(original_filename)
        elif naming_option == "Use Sheet Name":
            table_name = clean_column_name(selected_sheet)
        else:
            table_name = st.text_input("Enter Table Name", value=clean_column_name(selected_sheet))
        st.info(f"DB Table: `{table_name}`")

    with col2:
        st.subheader("📥 Insert Mode")
        insert_mode = st.radio(
            "What to do if table exists?",
            ["Replace (Overwrite Table)", "Append (Add to Existing)"],
            help="'Replace' will drop the old table. 'Append' will keep existing data."
        )
        sql_mode = "replace" if "Replace" in insert_mode else "append"

    # 3. Transform Column Names (Handle Duplicates here)
    new_column_names = make_columns_unique(df.columns)
    df_transformed = df.copy()
    df_transformed.columns = new_column_names
    
    st.subheader("✨ Transformed Data Preview (Snake Case & Unique Columns)")
    st.dataframe(df_transformed.head())
    
    # 4. Run ETL
    if st.button("🔥 Run ETL (Push to Database)"):
        with st.status("🚀 Processing ETL...", expanded=True) as status:
            try:
                conn_url = get_connection_url()
                if not conn_url:
                    st.error("Invalid database configuration.")
                    status.update(label="❌ ETL Failed", state="error")
                else:
                    status.write("🔌 Connecting to Database...")
                    engine = create_engine(conn_url)
                    
                    with engine.connect() as conn:
                        status.write("✅ Database Connected!")
                        status.write(f"📤 Pushing {len(df_transformed)} rows to table `{table_name}` using `{sql_mode}` mode...")
                        
                        # Use chunksize for efficiency on large files
                        df_transformed.to_sql(table_name, con=engine, if_exists=sql_mode, index=False, chunksize=1000)
                        
                        status.update(label="🎊 ETL Successfully Completed!", state="complete", expanded=False)
                        st.balloons()
                        st.success(f"Successfully uploaded data to table `{table_name}` ({sql_mode})!")
                        
            except Exception as e:
                st.error(f"❌ Error during ETL: {str(e)}")
                status.update(label="❌ ETL Failed", state="error")

else:
    st.info("Please upload an Excel file to start.")

st.markdown("---")
st.caption("Built with ❤️ using Streamlit & Pandas")
