import re
import pandas as pd
from typing import List, Tuple, Dict, Any


def clean_column_name(column_name: Any) -> str:
    """
    Transforms any raw column header into a standardized snake_case format.
    
    Rules:
    - Strips whitespace
    - Converts to lowercase
    - Replaces special and non-alphanumeric characters with an underscore
    - Collapses consecutive underscores into a single underscore
    - Strips leading and trailing underscores
    - Returns 'unnamed_column' if the resulting string is empty
    """
    if column_name is None:
        return "unnamed_column"

    clean_name = str(column_name).strip().lower()
    clean_name = re.sub(r'[^a-z0-9]', '_', clean_name)
    clean_name = re.sub(r'_+', '_', clean_name)
    clean_name = clean_name.strip('_')

    return clean_name if clean_name else "unnamed_column"


def make_columns_unique(columns: List[Any]) -> List[str]:
    """
    Ensures all column headers in a list are sanitized snake_case and strictly unique.
    Duplicates are suffixed with '_duplicate1', '_duplicate2', etc.
    """
    seen: Dict[str, int] = {}
    new_cols: List[str] = []

    for col in columns:
        base_name = clean_column_name(col)
        if base_name in seen:
            seen[base_name] += 1
            new_cols.append(f"{base_name}_duplicate{seen[base_name]}")
        else:
            seen[base_name] = 0
            new_cols.append(base_name)

    return new_cols


def clean_dataframe(
    df: pd.DataFrame,
    drop_empty_rows: bool = True,
    drop_empty_cols: bool = True,
    strip_whitespace: bool = True,
    nullify_nan: bool = True
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Performs robust data cleansing on a DataFrame:
    1. Removes completely empty rows
    2. Removes completely empty columns
    3. Trims whitespace from all string/object cells
    4. Replaces NaN / NaT values with Python None for standard database NULL compatibility
    
    Returns:
        Tuple[pd.DataFrame, Dict[str, int]]: (cleaned DataFrame, summary statistics dict)
    """
    df_clean = df.copy()
    initial_rows = len(df_clean)
    initial_cols = len(df_clean.columns)

    # 1. Drop completely empty rows
    if drop_empty_rows and initial_rows > 0:
        df_clean.dropna(how='all', inplace=True)
    rows_after_drop = len(df_clean)
    empty_rows_dropped = initial_rows - rows_after_drop

    # 2. Drop completely empty columns
    if drop_empty_cols and initial_cols > 0:
        df_clean.dropna(axis=1, how='all', inplace=True)
    cols_after_drop = len(df_clean.columns)
    empty_cols_dropped = initial_cols - cols_after_drop

    # 3. Strip whitespace from string/object columns
    if strip_whitespace:
        for col in df_clean.columns:
            if df_clean[col].dtype == "object":
                df_clean[col] = df_clean[col].apply(
                    lambda v: v.strip() if isinstance(v, str) else v
                )

    # 4. Convert NaN to None for SQL NULL compatibility
    if nullify_nan:
        df_clean = df_clean.where(pd.notnull(df_clean), None)

    stats = {
        "initial_rows": initial_rows,
        "final_rows": rows_after_drop,
        "empty_rows_dropped": empty_rows_dropped,
        "initial_cols": initial_cols,
        "final_cols": cols_after_drop,
        "empty_cols_dropped": empty_cols_dropped,
    }

    return df_clean, stats


def normalize_dataframe_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies snake_case transformation and duplicate resolution to DataFrame columns.
    """
    df_transformed = df.copy()
    df_transformed.columns = make_columns_unique(df.columns)
    return df_transformed
