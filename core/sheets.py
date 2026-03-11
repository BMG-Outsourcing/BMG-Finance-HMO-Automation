"""
core/sheets.py
==============
All Google Sheets read/write logic.
No Streamlit imports — pure I/O, fully testable.

Credentials come from st.secrets at the call site (app.py),
so this module stays framework-agnostic.

Dependencies: gspread, google-auth
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from config.constants import (
    REF_COL_NUM,
    REF_COL_ID,
    REF_COL_NAME,
    REF_COL_ENTITY,
    GSHEET_WORKSHEET_NAME,
)

# OAuth scopes required for read + write access
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ── Auth ──────────────────────────────────────────────────────────────────────

def _get_client(service_account_info: dict) -> gspread.Client:
    """
    Build and return an authenticated gspread client from a service account
    credentials dict (sourced from st.secrets["gcp_service_account"]).
    """
    creds = Credentials.from_service_account_info(service_account_info, scopes=_SCOPES)
    return gspread.authorize(creds)


# ── Read ──────────────────────────────────────────────────────────────────────

def load_reference_from_sheet(
    service_account_info: dict,
    spreadsheet_id: str,
) -> pd.DataFrame:
    """
    Read the reference worksheet from Google Sheets and return a clean DataFrame.

    Expected sheet columns: #  |  Id Number  |  Name  |  Entity
    Rows with a missing / blank Id Number are dropped automatically.

    Returns a DataFrame with columns: [Id Number, Name, Entity]
    """
    client      = _get_client(service_account_info)
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet   = spreadsheet.worksheet(GSHEET_WORKSHEET_NAME)

    # get_all_records() uses the first row as column headers
    records = worksheet.get_all_records(expected_headers=[
        REF_COL_NUM, REF_COL_ID, REF_COL_NAME, REF_COL_ENTITY
    ])

    df = pd.DataFrame(records)

    # Drop rows without a valid Id Number
    df = df[
        df[REF_COL_ID].notna()
        & (df[REF_COL_ID].astype(str).str.strip() != "")
    ].copy()

    # Return only the three meaningful columns
    return df[[REF_COL_ID, REF_COL_NAME, REF_COL_ENTITY]].reset_index(drop=True)


# ── Write ─────────────────────────────────────────────────────────────────────

def save_reference_to_sheet(
    service_account_info: dict,
    spreadsheet_id: str,
    updated_df: pd.DataFrame,
) -> None:
    """
    Overwrite the reference worksheet with the updated DataFrame.

    The sheet is completely cleared first, then re-written with:
      Row 1 : column headers  (#, Id Number, Name, Entity)
      Rows 2+: data rows, re-numbered from 1

    Args:
        service_account_info : dict from st.secrets["gcp_service_account"]
        spreadsheet_id       : the Google Sheet ID string
        updated_df           : DataFrame with columns [Id Number, Name, Entity]
    """
    client      = _get_client(service_account_info)
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet   = spreadsheet.worksheet(GSHEET_WORKSHEET_NAME)

    # Re-number the # column from 1
    write_df = updated_df[[REF_COL_ID, REF_COL_NAME, REF_COL_ENTITY]].copy().reset_index(drop=True)
    write_df.insert(0, REF_COL_NUM, range(1, len(write_df) + 1))

    # Build list-of-lists: header row + data rows
    headers   = write_df.columns.tolist()
    data_rows = write_df.astype(str).values.tolist()
    all_rows  = [headers] + data_rows

    # Clear and rewrite
    worksheet.clear()
    worksheet.update(all_rows, value_input_option="RAW")