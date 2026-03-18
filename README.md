# BMG Finance — HMO Billing Processor

A web-based tool built for **BMG Outsourcing INC.** that automates the processing of monthly HMO billing files — comparing them against a master employee reference list, flagging workforce changes, and splitting the billing into separate sheets per company entity.

---

## What It Does

Each billing cycle, the HMO provider sends a raw Excel file listing every covered employee and their charges. This tool takes that file and:

1. Validates the billing rows
2. Detects any employees who are new or no longer active
3. Updates the master reference list to reflect those changes
4. Assigns each billing row its correct company entity
5. Splits the entire billing into a separate sheet per entity — ready for distribution

---

## The Reference List

At the heart of the workflow is a **master reference list** — a maintained record of every covered employee with three pieces of information: their **ID number**, their **Name**, and which **Entity** (company) they belong to.

This reference is the single source of truth for entity assignment. The entity column that comes in the raw billing file is always discarded and replaced with the one from the reference.

The reference list can be stored in two places depending on the environment:

- **Google Sheets** (when deployed) — loaded and written back automatically using a service account
- **Local Excel file** (`data/reference.xlsx`) — used as a fallback during local development

---

## The Workflow

### Step 1 — Load Reference & Upload Billing File

The reference list is loaded automatically in the background as soon as the tool opens — no manual action needed. The user then uploads the raw billing Excel file from the HMO provider.

Only rows with a properly formatted employee ID (matching the pattern `XXXX-XXXXX-XX-XX`) are kept. Everything else — blank rows, summary rows, headers — is discarded.

---

### Step 2 — Sanity Check

The tool counts and previews the valid billing rows to confirm the file was read correctly before any processing begins. If no valid rows are found, the tool stops and alerts the user.

---

### Step 3 — Sync Preview

The tool compares every employee ID in the billing file against the reference list and surfaces two groups:

| Group | Meaning |
|---|---|
| **New Employees** | ID is in the billing file but not in the reference — they need to be added |
| **Missing Employees** | ID is in the reference but absent from the billing file — they may have left |

Both groups are shown as expandable previews with names and IDs so the user can review them before committing any changes.

---

### Step 4 — Process & Segregate

When the user clicks **Run Processing**, four things happen in sequence:

**4a — Update the reference list**
New employees are added to the reference (with their Entity left blank to be filled in manually later). Missing employees are removed. This keeps the reference in sync with the current billing cycle.

**4b — Write back to Google Sheets** *(cloud only)*
If the tool is running in deployed mode, the updated reference is automatically saved back to Google Sheets — no manual export or upload needed.

**4c — Assign entities**
Every row in the billing file is matched to its employee ID in the (now updated) reference, and the correct Entity is written into the billing data. Employees not found in the reference get a blank entity.

**4d — Segregate into sheets**
The billing data is split into separate sheets based on entity:

- **Advances sheet** — any row whose entity contains the word "advance" is pulled out into a dedicated sheet. On this sheet, the Entity column is replaced with the employee's Name, since advances are tracked per person rather than per company.
- **One sheet per Entity** — all remaining rows are grouped by their entity name, sorted alphabetically, with each entity becoming its own sheet.
- **Unknown sheet** — rows that couldn't be matched to any entity land here.

---

### Step 5 — Download Results

Two files are available for download:

| File | Contents |
|---|---|
| `segregated_billing.xlsx` | Multi-sheet workbook — one tab per entity (plus Advances) |
| `updated_reference.xlsx` | The updated master list reflecting this cycle's additions and removals |

When running on Google Sheets, the reference is already saved to the cloud automatically. The downloadable reference file serves as a local backup copy in that case.

---

## Reference Viewer Tab

A second tab in the tool shows a live view of the master reference data as it currently exists in memory — including the total record count and how many employees were added or removed in this session. Useful for a quick sanity check after processing.

---

## Intended Use

This tool is designed for the finance team at BMG Outsourcing INC. to process monthly HMO billing files efficiently — replacing the manual work of cross-referencing employee lists, updating records, and splitting out billing by entity every billing cycle.
