import os
import pytest
import pandas as pd
import numpy as np

from cleaner import (
    clean_column_name,
    make_columns_unique,
    clean_dataframe,
    normalize_dataframe_headers
)


class TestColumnSanitization:
    """Tests for individual and batch column name standardization into snake_case."""

    def test_clean_column_name_basic(self):
        assert clean_column_name("Customer Name") == "customer_name"
        assert clean_column_name("First_Name") == "first_name"
        assert clean_column_name("OrderID") == "orderid"
        assert clean_column_name("order_id") == "order_id"

    def test_clean_column_name_special_characters_and_symbols(self):
        assert clean_column_name("Order & Shipping # (USD)") == "order_shipping_usd"
        assert clean_column_name("Unit Price ($/hr)") == "unit_price_hr"
        assert clean_column_name("Discount %") == "discount"
        assert clean_column_name("Item---Code___SKU") == "item_code_sku"
        assert clean_column_name("   Total    Amount   ") == "total_amount"

    def test_clean_column_name_empty_or_invalid(self):
        assert clean_column_name("") == "unnamed_column"
        assert clean_column_name("   ") == "unnamed_column"
        assert clean_column_name(None) == "unnamed_column"
        assert clean_column_name("!@#$%^&*()") == "unnamed_column"
        assert clean_column_name("___") == "unnamed_column"

    def test_make_columns_unique_with_duplicates(self):
        raw_cols = ["Email", "email", "EMAIL", "Phone Number", "Phone Number"]
        expected = ["email", "email_duplicate1", "email_duplicate2", "phone_number", "phone_number_duplicate1"]
        assert make_columns_unique(raw_cols) == expected

    def test_make_columns_unique_with_empty_headers(self):
        raw_cols = ["", "   ", "Data", ""]
        expected = ["unnamed_column", "unnamed_column_duplicate1", "data", "unnamed_column_duplicate2"]
        assert make_columns_unique(raw_cols) == expected


class TestDataFrameCleansing:
    """Tests for DataFrame cleaning operations: empty rows/cols, whitespace trimming, and nullification."""

    def test_clean_dataframe_drops_empty_rows(self):
        data = {
            "name": ["Alice", None, "Bob", None],
            "age": [25, None, 30, None],
            "city": ["New York", None, "London", None]
        }
        df = pd.DataFrame(data)
        cleaned_df, stats = clean_dataframe(df)

        assert len(cleaned_df) == 2
        assert stats["empty_rows_dropped"] == 2
        assert list(cleaned_df["name"]) == ["Alice", "Bob"]

    def test_clean_dataframe_drops_empty_columns(self):
        data = {
            "id": [1, 2, 3],
            "empty_notes": [None, None, None],
            "amount": [100.0, 200.0, 300.0],
            "unnamed_all_nan": [np.nan, np.nan, np.nan]
        }
        df = pd.DataFrame(data)
        cleaned_df, stats = clean_dataframe(df)

        assert stats["empty_cols_dropped"] == 2
        assert set(cleaned_df.columns) == {"id", "amount"}

    def test_clean_dataframe_strips_string_whitespace(self):
        data = {
            "customer": ["  Alice Cooper  ", "Bob Marley   ", "   Charlie  "],
            "city": [" Jakarta  ", "Surabaya", "  Bandung "],
            "score": [95, 88, 72]  # Numeric column should remain untouched
        }
        df = pd.DataFrame(data)
        cleaned_df, _ = clean_dataframe(df)

        assert list(cleaned_df["customer"]) == ["Alice Cooper", "Bob Marley", "Charlie"]
        assert list(cleaned_df["city"]) == ["Jakarta", "Surabaya", "Bandung"]
        assert list(cleaned_df["score"]) == [95, 88, 72]

    def test_clean_dataframe_converts_nan_to_none_for_sql(self):
        data = {
            "id": [1, 2],
            "description": ["Item 1", np.nan]
        }
        df = pd.DataFrame(data)
        cleaned_df, _ = clean_dataframe(df)

        # None is essential for SQLAlchemy to correctly write SQL NULL
        assert cleaned_df.loc[1, "description"] is None

    def test_normalize_dataframe_headers(self):
        data = {
            "  Order ID # ": [1, 2],
            "Customer Email": ["a@x.com", "b@x.com"],
            "Customer Email": ["alt_a@x.com", "alt_b@x.com"],  # python dict will overwrite key, so create with df constructor
        }
        raw_df = pd.DataFrame([[1, "a@x.com", "alt_a@x.com"], [2, "b@x.com", "alt_b@x.com"]])
        raw_df.columns = ["  Order ID # ", "Customer Email", "Customer Email"]

        normalized_df = normalize_dataframe_headers(raw_df)
        assert list(normalized_df.columns) == ["order_id", "customer_email", "customer_email_duplicate1"]


class TestRealWorldSampleDataset:
    """Integration test validating that the generated messy sample dataset cleans cleanly."""

    def test_clean_messy_csv_sample(self):
        sample_path = os.path.join(os.path.dirname(__file__), "..", "samples", "messy_sales_data.csv")
        assert os.path.exists(sample_path), f"Sample file not found at {sample_path}"

        raw_df = pd.read_csv(sample_path)
        initial_raw_rows = len(raw_df)

        # Apply cleaning pipeline
        cleaned_df, stats = clean_dataframe(raw_df)
        transformed_df = normalize_dataframe_headers(cleaned_df)

        # Verify empty rows were removed
        assert stats["empty_rows_dropped"] == 2
        assert len(transformed_df) == initial_raw_rows - 2

        # Verify empty column was removed
        assert stats["empty_cols_dropped"] == 1

        # Verify standardized column names (snake_case + unique)
        expected_cols = [
            "order_id",
            "customer_name",
            "order_date",
            "product_category",
            "unit_price",
            "qty",
            "customer_email",
            "customer_email_duplicate1",
            "notes_remarks"
        ]
        assert list(transformed_df.columns) == expected_cols

        # Verify untrimmed whitespace was cleaned
        assert transformed_df["customer_name"].iloc[0] == "Acme Corp"
        assert transformed_df["customer_name"].iloc[5] == "Stark Industries"

    def test_clean_messy_excel_sample(self):
        sample_path = os.path.join(os.path.dirname(__file__), "..", "samples", "messy_sales_data.xlsx")
        assert os.path.exists(sample_path), f"Excel sample not found at {sample_path}"

        xl = pd.ExcelFile(sample_path)
        assert "Sales Transactions" in xl.sheet_names
        assert "Region Reference" in xl.sheet_names

        df = pd.read_excel(sample_path, sheet_name="Sales Transactions")
        cleaned_df, stats = clean_dataframe(df)
        transformed_df = normalize_dataframe_headers(cleaned_df)

        assert stats["empty_rows_dropped"] == 2
        assert stats["empty_cols_dropped"] == 1
        assert "customer_name" in transformed_df.columns
        assert transformed_df["customer_name"].iloc[0] == "Acme Corp"
