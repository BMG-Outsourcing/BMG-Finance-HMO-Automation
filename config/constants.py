"""
config/constants.py
===================
All application-wide constants. Change values here to affect the entire app.
Never scatter magic strings or numbers throughout the codebase.
"""

# App Identity ─────────────────────────────────────────────────────────────
APP_TITLE       = "Billing Processor"
APP_ICON        = "🧾"
APP_SUBTITLE    = "Process, compare, and segregate Excel billing files — entirely in memory."

# Tab Labels 
TAB_PROCESSOR = "Billing Processor"
TAB_REFERENCE = "Reference Viewer"

# Step Labels 
STEP_1_LABEL = "Upload Files"
STEP_2_LABEL = "Sanity Check"
STEP_3_LABEL = "Sync Preview"
STEP_4_LABEL = "Process"
STEP_5_LABEL = "Download"

# Keyword Filters (Step 2)
BILLING_KEYWORDS = ["MONTHLY", "Additional billing"]

# Column Name Candidates
ID_COLUMN_CANDIDATES   = ["id number", "id", "employee id", "emp id", "employee no", "emp no"]
NAME_COLUMN_CANDIDATES = ["name", "employee name", "full name", "emp name"]
ENTITY_COLUMN_CANDIDATES = ["entity", "company", "department"]
SUBJECT_COLUMN_CANDIDATES = ["subject", "description", "particulars", "details", "remarks", "memo"]

# Reference File Expected Columns 
REF_EXPECTED_COLUMNS = ["ID Number", "Name", "Entity"]

# Segregation 
ADVANCES_KEYWORD   = "advance"          # Entity value substring → Advances sheet
ADVANCES_SHEET_NAME = "Advances"        # Exact name of the Advances sheet
UNKNOWN_ENTITY_SHEET = "Unknown"        # Fallback sheet name for blank Entity

# Excel Constraints 
EXCEL_SHEET_NAME_MAX_LEN  = 31
EXCEL_SHEET_INVALID_CHARS = r'[\\/*?\[\]:]'

# Reference File Path
import os as _os
REFERENCE_FILE_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "data", "reference.xlsx")

# Download Filenames 
DOWNLOAD_BILLING_FILENAME   = "segregated_billing.xlsx"
DOWNLOAD_REFERENCE_FILENAME = "updated_reference.xlsx"
DOWNLOAD_BILLING_LABEL      = "Download Segregated Billing"
DOWNLOAD_REFERENCE_LABEL    = "Download Updated Reference"

# MIME Type 
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Session State Keys 
SK_REF_DF           = "ref_df"
SK_RAW_DF           = "raw_df"
SK_FILTERED_DF      = "filtered_df"
SK_UPDATED_REF_DF   = "updated_ref_df"
SK_NEW_EMPLOYEES    = "new_employees"
SK_MISSING_EMPLOYEES= "missing_employees"
SK_PROCESSED        = "processed"
SK_SEGREGATED_BYTES = "segregated_bytes"
SK_UPDATED_REF_BYTES= "updated_ref_bytes"
SK_REF_NAME         = "_ref_name"
SK_RAW_NAME         = "_raw_name"

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