# 🚀 SheetPusher: The Python Excel-to-Database ETL Tool

**SheetPusher** is a lightweight, Streamlit-powered tool to automatically convert your messy Excel files into clean database tables in seconds.

## ✨ Key Features

- **Automatic Snake Case Conversion**: Converts column headers from "Total Price" to `total_price` automatically.
- **Smart Cleansing**: Removes empty rows and columns, and trims whitespace from data.
- **Sheet Selector**: Choose any sheet from your workbook.
- **Column Selection**: Pick exactly which columns you want to import.
- **Duplicate Handler**: Automatically handles duplicate column names (e.g., `sales`, `sales_duplicate1`).
- **Multiple Dialects**: Supports **MariaDB**, **MySQL**, **PostgreSQL**, **SQLite**, and **MSSQL**.
- **Append vs Replace**: Choose to overwrite existing tables or add data to them.
- **Connection Profiles**: Save your database credentials locally for quick access.

## 🌐 Cloud vs Local Execution

| Feature | Streamlit Cloud | Local Execution (Recommended) |
|---------|-----------------|-------------------------------|
| **Database Access** | Cloud DBs only (AWS, Supabase, etc.) | **Local DBs (localhost)** & Cloud DBs |
| **Privacy** | Data processed on Streamlit servers | Data stays on your machine |
| **Setup** | No installation needed | Requires Python & Pip |

> **⚠️ IMPORTANT:** If you want to connect to a database running on your own computer (**localhost**), you **must** run SheetPusher locally. The cloud version cannot "see" your local machine's network.

## 🛠️ Installation (For Local Use)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/fauzanlm/SheetPusher.git
   cd SheetPusher
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python -m streamlit run app.py
   ```

## 🖥️ Usage

1. Open the UI in your browser (usually `http://localhost:8501`).
2. Configure your database settings in the sidebar.
3. Click "Save Database Profile" to remember your settings.
4. Upload an Excel file (`.xlsx` or `.xls`).
5. Choose your sheet and columns.
6. Set your table name and insert mode (Replace/Append).
7. Click **Run ETL** and watch the magic happen!

## 🔐 Privacy & Security

SheetPusher saves your database credentials locally in a `db_config.json` file. This file is ignored by `.gitignore` to ensure your passwords are never pushed to GitHub.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
Built with ❤️ by [fauzanlm](https://github.com/fauzanlm)
