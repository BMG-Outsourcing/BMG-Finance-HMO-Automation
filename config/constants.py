"""
config/constants.py
===================
All application-wide constants. Change values here to affect the entire app.
Never scatter magic strings or numbers throughout the codebase.
"""

# ── App Identity ──────────────────────────────────────────────────────────────
APP_TITLE    = "Billing Processor"
APP_ICON     = "🧾"
APP_SUBTITLE = "Process, compare, and segregate Excel billing files — entirely in memory."

# ── Tab Labels ────────────────────────────────────────────────────────────────
TAB_PROCESSOR = "Billing Processor"
TAB_REFERENCE = "Reference Viewer"

# ── Keyword Filters (Step 2 sanity check) ────────────────────────────────────
BILLING_KEYWORDS = ["MONTHLY", "Additional billing"]

# ── Exact column names (hardwired from real files) ───────────────────────────
# Google Sheet / reference — columns are: #, Id Number, Name, Entity
REF_HEADER_ROW = 11
REF_COL_NUM    = "#"
REF_COL_ID     = "Id Number"
REF_COL_NAME   = "Name"
REF_COL_ENTITY = "Entity"

# Billing file — entity lives in the last column labelled "Unnamed: 30"
BIL_COL_ID     = "Id Number"
BIL_COL_NAME   = "Name"
BIL_COL_ENTITY = "Unnamed: 30"   # renamed → "Entity" on load

# ── Reference file (local fallback only — not used on Streamlit Cloud) ───────
import os as _os
REFERENCE_FILE_PATH = _os.path.join(
    _os.path.dirname(_os.path.dirname(__file__)), "data", "reference.xlsx"
)

# ── Google Sheets constants ───────────────────────────────────────────────────
# The worksheet name inside the spreadsheet that holds the reference data.
# All other sheets in the same spreadsheet are ignored.
GSHEET_WORKSHEET_NAME = "Reference"

# Streamlit secret keys — must match exactly what you put in st.secrets
GSHEET_SECRET_KEY        = "gcp_service_account"   # the [gcp_service_account] block
GSHEET_SPREADSHEET_KEY   = "spreadsheet_id"         # key inside [google_sheets]
GSHEET_SECTION           = "google_sheets"           # section name in secrets.toml

# ── Segregation ───────────────────────────────────────────────────────────────
ADVANCES_KEYWORD    = "advance"
ADVANCES_SHEET_NAME = "Advances"
UNKNOWN_ENTITY_SHEET = "Unknown"

# ── Excel constraints ─────────────────────────────────────────────────────────
EXCEL_SHEET_NAME_MAX_LEN  = 31
EXCEL_SHEET_INVALID_CHARS = r'[\\/*?\[\]:]'

# ── Download filenames ────────────────────────────────────────────────────────
DOWNLOAD_BILLING_FILENAME   = "segregated_billing.xlsx"
DOWNLOAD_REFERENCE_FILENAME = "updated_reference.xlsx"
DOWNLOAD_BILLING_LABEL      = "Download Segregated Billing"
DOWNLOAD_REFERENCE_LABEL    = "Download Updated Reference"

# ── MIME ─────────────────────────────────────────────────────────────────────
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# ── Session state keys ────────────────────────────────────────────────────────
SK_REF_DF            = "ref_df"
SK_RAW_DF            = "raw_df"
SK_FILTERED_DF       = "filtered_df"
SK_UPDATED_REF_DF    = "updated_ref_df"
SK_NEW_EMPLOYEES     = "new_employees"
SK_MISSING_EMPLOYEES = "missing_employees"
SK_PROCESSED         = "processed"
SK_SEGREGATED_BYTES  = "segregated_bytes"
SK_UPDATED_REF_BYTES = "updated_ref_bytes"
SK_REF_NAME          = "_ref_name"
SK_RAW_NAME          = "_raw_name"

SESSION_DEFAULTS: dict = {
    SK_REF_DF:            None,
    SK_RAW_DF:            None,
    SK_FILTERED_DF:       None,
    SK_UPDATED_REF_DF:    None,
    SK_NEW_EMPLOYEES:     [],
    SK_MISSING_EMPLOYEES: [],
    SK_PROCESSED:         False,
    SK_SEGREGATED_BYTES:  None,
    SK_UPDATED_REF_BYTES: None,
    SK_REF_NAME:          "",
    SK_RAW_NAME:          "",
}