"""
core/processor.py
=================
Pure business-logic functions.
No Streamlit imports — fully testable in isolation.
All Excel I/O uses in-memory io.BytesIO buffers.
"""

import io
import re
import pandas as pd

from config.constants import (
    EXCEL_SHEET_INVALID_CHARS,
    EXCEL_SHEET_NAME_MAX_LEN,
    ADVANCES_KEYWORD,
    ADVANCES_SHEET_NAME,
    UNKNOWN_ENTITY_SHEET,
    BILLING_KEYWORDS,
)


# Column Utilities 

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing whitespace from all column names."""
    df.columns = df.columns.str.strip()
    return df


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """
    Case-insensitive search through `candidates` to find the first match
    in the DataFrame's actual column names. Returns the real column name or None.
    """
    lower_map = {c.lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


# Excel I/O 

def read_excel_to_df(uploaded_file) -> pd.DataFrame:
    """Read an uploaded Streamlit UploadedFile into a pandas DataFrame."""
    return pd.read_excel(uploaded_file, engine="openpyxl")


def sanitize_sheet_name(name: str) -> str:
    """
    Produce a valid Excel sheet name:
      - Remove characters: / \\ * ? [ ] :
      - Truncate to EXCEL_SHEET_NAME_MAX_LEN characters
      - Fall back to 'Sheet' if the result is empty
    """
    clean = re.sub(EXCEL_SHEET_INVALID_CHARS, "", str(name)).strip()
    return clean[:EXCEL_SHEET_NAME_MAX_LEN] if clean else "Sheet"


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    """Serialise a single DataFrame to an Excel workbook in memory."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


def multi_sheet_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    """
    Serialise a mapping of {sheet_name: DataFrame} into a multi-sheet
    Excel workbook entirely in memory. Sheet names are sanitized automatically.
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for raw_name, df in sheets.items():
            safe = sanitize_sheet_name(raw_name)
            df.to_excel(writer, index=False, sheet_name=safe)
    return buf.getvalue()


# Step 2: Keyword Filter 

def filter_billing_rows(
    raw_df: pd.DataFrame,
    subject_col: str,
    keywords: list[str] | None = None,
) -> pd.DataFrame:
    """
    Return only the rows whose `subject_col` contains at least one keyword
    from `keywords` (case-insensitive). Defaults to BILLING_KEYWORDS constant.
    """
    if keywords is None:
        keywords = BILLING_KEYWORDS

    mask = pd.Series([False] * len(raw_df), index=raw_df.index)
    for kw in keywords:
        mask |= raw_df[subject_col].astype(str).str.contains(kw, case=False, na=False)
    return raw_df[mask].copy()


# Step 3: Sync Analysis 

def compare_employees(
    filtered_df: pd.DataFrame,
    ref_df: pd.DataFrame,
    raw_id_col: str,
    ref_id_col: str,
) -> tuple[set[str], set[str]]:
    """
    Return (new_ids, missing_ids):
      new_ids     — IDs in billing but absent from reference
      missing_ids — IDs in reference but absent from billing
    """
    raw_ids = set(filtered_df[raw_id_col].dropna().astype(str).str.strip())
    ref_ids = set(ref_df[ref_id_col].dropna().astype(str).str.strip())
    return raw_ids - ref_ids, ref_ids - raw_ids


# Step 4: Core Processing 

def update_reference(
    ref_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
    ref_id_col: str,
    ref_name_col: str,
    ref_entity_col: str | None,
    raw_id_col: str,
    raw_name_col: str,
    new_ids: set[str],
    missing_ids: set[str],
) -> pd.DataFrame:
    """
    Produce an updated reference DataFrame by:
      1. Removing rows whose ID appears in `missing_ids`
      2. Appending new rows for every ID in `new_ids` (Entity left blank)
    """
    updated = ref_df.copy()

    # Remove missing employees
    updated = updated[
        ~updated[ref_id_col].astype(str).str.strip().isin(missing_ids)
    ].copy()

    # Add new employees
    if new_ids:
        new_rows = (
            filtered_df[filtered_df[raw_id_col].astype(str).str.strip().isin(new_ids)]
            [[raw_id_col, raw_name_col]]
            .drop_duplicates()
            .copy()
        )
        new_rows.rename(columns={raw_id_col: ref_id_col, raw_name_col: ref_name_col}, inplace=True)
        if ref_entity_col:
            new_rows[ref_entity_col] = ""
        updated = pd.concat([updated, new_rows], ignore_index=True)

    return updated


def merge_entity(
    billing: pd.DataFrame,
    updated_ref: pd.DataFrame,
    raw_id_col: str,
    ref_id_col: str,
    ref_entity_col: str,
) -> pd.DataFrame:
    """
    Drop any pre-existing entity column from billing, then left-join the
    'Entity' column from updated_ref using the employee ID as the key.
    """
    billing = billing.copy()

    # Remove stale entity column to avoid _x/_y suffixes
    for col in billing.columns:
        if col.lower() in {"entity", "company", "department"}:
            billing.drop(columns=[col], inplace=True)

    entity_lookup = (
        updated_ref[[ref_id_col, ref_entity_col]]
        .drop_duplicates(subset=[ref_id_col])
        .rename(columns={ref_id_col: raw_id_col, ref_entity_col: "Entity"})
    )
    entity_lookup[raw_id_col] = entity_lookup[raw_id_col].astype(str).str.strip()
    billing[raw_id_col]       = billing[raw_id_col].astype(str).str.strip()

    return billing.merge(entity_lookup, on=raw_id_col, how="left")


def segregate_billing(
    billing: pd.DataFrame,
    raw_name_col: str,
) -> dict[str, pd.DataFrame]:
    """
    Split the merged billing DataFrame into sheets:
      - ADVANCES_SHEET_NAME : rows whose Entity contains ADVANCES_KEYWORD
          (Entity column replaced with the employee's Name)
      - One sheet per distinct Entity value for all other rows
    Returns an ordered dict: Advances first, then company sheets alphabetically.
    """
    sheets: dict[str, pd.DataFrame] = {}

    advance_mask = billing["Entity"].astype(str).str.contains(
        ADVANCES_KEYWORD, case=False, na=False
    )
    advances_df = billing[advance_mask].copy()
    company_df  = billing[~advance_mask].copy()

    if not advances_df.empty:
        advances_df["Entity"] = advances_df[raw_name_col].astype(str)
        sheets[ADVANCES_SHEET_NAME] = advances_df.reset_index(drop=True)

    for entity, group in company_df.groupby("Entity", dropna=False, sort=True):
        sheet_name = (
            sanitize_sheet_name(str(entity))
            if pd.notna(entity) and str(entity).strip()
            else UNKNOWN_ENTITY_SHEET
        )
        sheets[sheet_name] = group.reset_index(drop=True)

    return sheets