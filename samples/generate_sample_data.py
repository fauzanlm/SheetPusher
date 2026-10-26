"""
Sample Data Generator for SheetPusher ETL Testing.
Generates intentionally messy CSV and Excel files reflecting real-world business spreadsheet issues:
- Untrimmed whitespace in text values
- Inconsistent date formats
- Duplicate column headers
- Dirty currency and numeric strings
- Duplicate records
- Completely empty rows and columns
- Missing / Null values
"""

import os
import pandas as pd
import openpyxl


def generate_samples(output_dir: str = "samples"):
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "messy_sales_data.csv")
    xlsx_path = os.path.join(output_dir, "messy_sales_data.xlsx")

    # Raw dirty data rows
    # Note: Column names contain weird whitespaces, special chars, and duplicate 'Customer Email'
    headers = [
        "  Order ID # ",
        " Customer Name  ",
        " Order Date ",
        "Product Category ",
        "  Unit Price ($) ",
        "Qty",
        "Customer Email",
        "Customer_Email",  # Colliding column header when normalized to snake_case
        "   ",             # Empty column header with all nulls
        "Notes / Remarks"
    ]

    data = [
        # Row 1: Normal clean-ish with slight whitespace
        ["ORD-1001", "  Acme Corp  ", "2024-01-15", "Electronics", "$1,200.00", 2, "billing@acme.com", "billing@acme.com", None, "Urgent delivery"],
        
        # Row 2: Inconsistent date format, dirty currency
        ["ORD-1002", "Globex Inc", "16/01/2024", "Office Supplies", "  45.50  ", 10, "orders@globex.org", "orders@globex.org", None, "  Net 30 terms  "],
        
        # Row 3: Missing email, whitespace in text
        ["ORD-1003", "  Soylent Corp ", "Jan 17, 2024", "Food & Beverage", "$15.00", 100, None, None, None, None],
        
        # Row 4: Completely empty row (all None)
        [None, None, None, None, None, None, None, None, None, None],
        
        # Row 5: Inconsistent date (dot format), dirty number
        ["ORD-1004", "Initech LLC", "2024.01.18", "Software", "$3,500.00", 1, "support@initech.com", "billing@initech.com", None, "Annual License"],
        
        # Row 6: Duplicate of Row 1 (duplicate row issue)
        ["ORD-1001", "  Acme Corp  ", "2024-01-15", "Electronics", "$1,200.00", 2, "billing@acme.com", "billing@acme.com", None, "Urgent delivery"],
        
        # Row 7: Untrimmed whitespaces in multiple columns, missing notes
        ["ORD-1005", "   Stark Industries   ", "2024-01-19", " Hardware ", "$899.90", 5, "tony@stark.com", "tony@stark.com", None, None],
        
        # Row 8: Another completely empty row
        [None, None, None, None, None, None, None, None, None, None],
        
        # Row 9: Date with dashes, dirty currency
        ["ORD-1006", "Wayne Enterprises", "20-01-2024", "Vehicles", "$45,000.00", 1, "bruce@wayne.com", "finance@wayne.com", None, "Confidential order"],
        
        # Row 10: Lowercase email, whitespace
        ["ORD-1007", " Cyberdyne Systems ", "2024/01/21", "AI & Robotics", "$12,400.00", 3, "skynet@cyberdyne.io", "info@cyberdyne.io", None, "Priority handling"]
    ]

    # Save to CSV
    # Note: write directly to keep duplicate column headers intact in raw file
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(",".join([f'"{h}"' for h in headers]) + "\n")
        for row in data:
            row_str = ",".join([f'"{val}"' if val is not None else "" for val in row])
            f.write(row_str + "\n")

    print(f"✅ Generated messy CSV sample: {csv_path}")

    # Save to Excel with openpyxl to preserve raw sheet structure and headers
    wb = openpyxl.Workbook()
    
    # Sheet 1: Messy Sales Data
    ws1 = wb.active
    ws1.title = "Sales Transactions"
    ws1.append(headers)
    for row in data:
        ws1.append(row)

    # Sheet 2: Clean Reference Data (to test multi-sheet workbook selector)
    ws2 = wb.create_sheet(title="Region Reference")
    ws2.append(["Region Code", "Region Name", "Manager"])
    ws2.append(["REG-01", "North America", "John Doe"])
    ws2.append(["REG-02", "Asia Pacific", "Siti Nurhaliza"])
    ws2.append(["REG-03", "Europe", "Jean Dupont"])

    wb.save(xlsx_path)
    print(f"✅ Generated messy Excel sample: {xlsx_path}")


if __name__ == "__main__":
    generate_samples()
