"""
core/processor.py
=================
Pure business-logic. No Streamlit imports.

The workflow is simple:
  1. Load reference master list  (Id Number, Name, Entity)
  2. Load raw billing file        (Id Number, Name, + other columns)
  3. For each row in billing, look up Id Number in reference → get Entity
  4. Add Entity as a new column in the billing file
  5. Segregate into sheets: Advances sheet + one sheet per Entity
"""

import io
import re
import pandas as pd

from config.constants import (
    REF_HEADER_ROW,
    REF_COL_ID, REF_COL_NAME, REF_COL_ENTITY,
    BIL_COL_ID, BIL_COL_NAME, BIL_COL_ENTITY,
    ADVANCES_KEYWORD, ADVANCES_SHEET_NAME, UNKNOWN_ENTITY_SHEET,
    EXCEL_SHEET_INVALID_CHARS, EXCEL_SHEET_NAME_MAX_LEN,
)


# ── Reference ─────────────────────────────────────────────────────────────────

def read_reference_df(path_or_file) -> pd.DataFrame:
    """
    Load the master reference file.

    Handles two formats:
      - Original format: 11-row header block, column headers at row 11
      - Clean format: column headers at row 0 (e.g. previously exported file)

    Only rows whose Id Number matches the real ID pattern are kept.
    Returns a clean DataFrame with columns: [Id Number, Name, Entity]
    """
    id_pattern = r'^\d{4}-\d{5}-\d{2}-\d{2}$'

    # Try clean format first (header at row 0)
    df = pd.read_excel(path_or_file, engine="openpyxl", header=0)
    df.columns = df.columns.str.strip()

    if REF_COL_ID not in df.columns:
        # Fall back to original format (header at row 11)
        df = pd.read_excel(path_or_file, engine="openpyxl", header=REF_HEADER_ROW)
        df.columns = df.columns.str.strip()

    # Keep only rows with a real ID (e.g. 5060-00011-00-00)
    mask = df[REF_COL_ID].astype(str).str.strip().str.match(id_pattern)
    df = df[mask][[REF_COL_ID, REF_COL_NAME, REF_COL_ENTITY]].copy()
    return df.reset_index(drop=True)


# ── Billing file ──────────────────────────────────────────────────────────────

def read_billing_df(path_or_file) -> pd.DataFrame:
    """
    Load the raw billing file.
    - Drops blank rows and summary rows (no valid Id Number).
    - Drops the last column (Unnamed: 30) — Entity is NOT taken from the
      billing file. It is always looked up from the reference master list.
    """
    df = pd.read_excel(path_or_file, engine="openpyxl", header=0)
    df.columns = df.columns.str.strip()

    # Drop the billing file's own entity column — reference is the source of truth
    if BIL_COL_ENTITY in df.columns:
        df.drop(columns=[BIL_COL_ENTITY], inplace=True)

    # Keep only rows with a real Id Number
    id_pattern = r'^\d{4}-\d{5}-\d{2}-\d{2}$'
    mask = df[BIL_COL_ID].astype(str).str.strip().str.match(id_pattern)
    df = df[mask].copy()

    return df.reset_index(drop=True)


# ── Core logic ────────────────────────────────────────────────────────────────

def compare_employees(
    billing_df: pd.DataFrame,
    ref_df: pd.DataFrame,
) -> tuple[set[str], set[str]]:
    """
    Compare Id Numbers between billing and reference.
    Returns:
      new_ids     — in billing but NOT in reference (need to be added)
      missing_ids — in reference but NOT in billing  (may have left)
    """
    bil_ids = set(billing_df[BIL_COL_ID].astype(str).str.strip())
    ref_ids = set(ref_df[REF_COL_ID].astype(str).str.strip())
    return bil_ids - ref_ids, ref_ids - bil_ids


def add_entity_column(
    billing_df: pd.DataFrame,
    ref_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    The core operation:
      For every row in billing_df, look up its Id Number in ref_df
      and write the matching Entity into a new 'Entity' column.

    Rows whose Id Number is not found in the reference get a blank Entity.
    """
    billing = billing_df.copy()

    # Build a clean lookup: Id Number → Entity
    lookup = (
        ref_df[[REF_COL_ID, REF_COL_ENTITY]]
        .drop_duplicates(subset=[REF_COL_ID])
        .copy()
    )
    lookup[REF_COL_ID] = lookup[REF_COL_ID].astype(str).str.strip()
    billing[BIL_COL_ID] = billing[BIL_COL_ID].astype(str).str.strip()

    # Left-join to add Entity column
    billing = billing.merge(
        lookup.rename(columns={REF_COL_ID: BIL_COL_ID, REF_COL_ENTITY: "Entity"}),
        on=BIL_COL_ID,
        how="left",
    )
    billing["Entity"] = billing["Entity"].fillna("")
    return billing


def update_reference(
    ref_df: pd.DataFrame,
    billing_df: pd.DataFrame,
    new_ids: set[str],
    missing_ids: set[str],
) -> pd.DataFrame:
    """
    Sync the reference master list:
      - Add new employees (Entity left blank — to be filled in manually)
      - Remove employees no longer in billing
    """
    updated = ref_df.copy()

    # Remove missing employees
    updated = updated[
        ~updated[REF_COL_ID].astype(str).str.strip().isin(missing_ids)
    ].copy()

    # Add new employees
    if new_ids:
        new_rows = (
            billing_df[billing_df[BIL_COL_ID].astype(str).str.strip().isin(new_ids)]
            [[BIL_COL_ID, BIL_COL_NAME]]
            .drop_duplicates()
            .copy()
        )
        new_rows.rename(columns={BIL_COL_ID: REF_COL_ID, BIL_COL_NAME: REF_COL_NAME}, inplace=True)
        new_rows[REF_COL_ENTITY] = ""
        updated = pd.concat([updated, new_rows], ignore_index=True)

    return updated


# ── Segregation ───────────────────────────────────────────────────────────────

def sanitize_sheet_name(name: str) -> str:
    clean = re.sub(EXCEL_SHEET_INVALID_CHARS, "", str(name)).strip()
    return clean[:EXCEL_SHEET_NAME_MAX_LEN] if clean else "Sheet"


def segregate_billing(billing: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Split billing rows into sheets:
      - 'Advances' sheet  : rows whose Entity contains 'advance'
          → Entity column replaced with the employee's Name
      - One sheet per Entity for all remaining rows (alphabetical)
    """
    sheets: dict[str, pd.DataFrame] = {}

    advance_mask = billing["Entity"].astype(str).str.contains(
        ADVANCES_KEYWORD, case=False, na=False
    )
    advances_df = billing[advance_mask].copy()
    company_df  = billing[~advance_mask].copy()

    if not advances_df.empty:
        advances_df["Entity"] = advances_df[BIL_COL_NAME].astype(str)
        sheets[ADVANCES_SHEET_NAME] = advances_df.reset_index(drop=True)

    for entity, group in company_df.groupby("Entity", dropna=False, sort=True):
        entity_str = str(entity).strip()
        sheet_name = sanitize_sheet_name(entity_str) if entity_str else UNKNOWN_ENTITY_SHEET
        sheets[sheet_name] = group.reset_index(drop=True)

    return sheets


# ── Excel I/O ─────────────────────────────────────────────────────────────────

def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


def multi_sheet_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for raw_name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=sanitize_sheet_name(raw_name))
    return buf.getvalue()