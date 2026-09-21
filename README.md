# ESG Carbon Compliance Copilot

A beginner-friendly FastAPI application for uploading ESG activity data, classifying emissions into GHG Protocol scopes, calculating CO₂e when an approved emission factor is available, and maintaining an audit trail.

> **Important:** The emission factors currently included in this project are marked `DEMO`. They must not be treated as official factors. Current results will normally be marked `REVIEW_REQUIRED` and will not produce verified emissions totals.

---

## Current capabilities

The project currently includes:

- A FastAPI backend.
- A browser-based dashboard.
- Manual carbon calculations.
- CSV activity uploads.
- Basic PDF text extraction.
- Keyword-based Scope 1, Scope 2, and Scope 3 classification.
- A deterministic emissions calculator.
- A SQLite audit log.
- Basic greenwashing-claim detection for PDF uploads.
- Optional Lyzr AI analysis using the configured AI provider.

The application is currently an MVP and is not yet a production compliance or regulatory reporting system.

---

## Project structure

```text
agents/
  esg_agent.py                 Lyzr AI agent configuration

backend/
  main.py                      FastAPI application entry point
  database.py                  SQLite audit database
  api/
    upload.py                  PDF and CSV upload processing
    emissions.py               Manual and AI analysis endpoints
    audit.py                   Audit summary and records endpoint
  services/
    classifier.py              Activity-to-scope classification
    calculator.py              Deterministic CO₂e calculation
    extraction.py              PDF text and activity extraction
    factor_service.py          Emission-factor lookup
    greenwashing.py            Basic sustainability-claim detection
  data/
    emission_factors.csv       Emission-factor data

frontend/
  index.html                   Dashboard markup
  app.js                      Frontend behavior and API calls
  style.css                   Dashboard styling

sample_data/
  sample_esg_data.csv          Sample CSV data

uploads/
                              Sample and uploaded documents

backend/esg_audit.db           SQLite audit database
```

Run all commands from the project root—the folder containing `backend`, `frontend`, and `agents`.

---

## Requirements

Install the following before starting the application:

- Windows PowerShell
- Python 3.10 or newer
- A Lyzr API key for the AI analysis feature

The current source code imports these Python packages:

- `fastapi`
- `uvicorn`
- `python-multipart`
- `pypdf`
- `python-dotenv`
- `lyzr-adk`

The project does not currently include a `requirements.txt` or `pyproject.toml`, so the dependencies must be installed manually.

---

## Windows PowerShell setup

### 1. Open PowerShell

Open PowerShell and move to the project directory.

Replace the path below with the actual location of this project:

```powershell
Set-Location "C:\Users\SUBHASREE\esg-carbon-copilot"
```

Confirm that you are in the correct directory:

```powershell
Get-ChildItem
```

You should see folders such as:

```text
agents
backend
frontend
sample_data
uploads
```

### 2. Create a virtual environment

```powershell
py -3 -m venv .venv
```

If the `py` command is not available, use:

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, the PowerShell prompt should show `(.venv)`.

If PowerShell blocks script execution, allow scripts only for the current PowerShell process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### 5. Install the project dependencies

```powershell
python -m pip install fastapi "uvicorn[standard]" python-multipart pypdf python-dotenv lyzr-adk
```

---

## Environment variables

The AI integration expects one environment variable:

```text
LYZR_API_KEY
```

The application loads variables from a `.env` file in the project root.

Create or edit a file named `.env` in the project root:

```text
LYZR_API_KEY=replace_with_your_lyzr_api_key
```

Replace the placeholder with a valid Lyzr API key.

### PowerShell-only alternative

Instead of using a `.env` file, set the variable for the current PowerShell session:

```powershell
$env:LYZR_API_KEY = "replace_with_your_lyzr_api_key"
```

This value will be cleared when the PowerShell window is closed.

### Security notes

- Do not commit `.env` to source control.
- Do not paste the API key into the frontend.
- Do not share the API key in screenshots, logs, or support requests.
- The deterministic calculation logic uses the local factor CSV, while the AI analysis endpoint uses the Lyzr configuration.

---

## Start the FastAPI application

Make sure the virtual environment is active and that PowerShell is still located at the project root.

Start the application with:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

You should see a message similar to:

```text
Uvicorn running on http://127.0.0.1:8000
```

Keep this PowerShell window open while using the application.

### Stop the application

Press:

```text
Ctrl+C
```

---

## Open the dashboard

Open a browser and visit:

```text
http://127.0.0.1:8000/
```

Do not open `frontend/index.html` directly from the file system. The FastAPI server must serve the frontend so that the dashboard can communicate with the backend API.

The FastAPI interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The alternative ReDoc documentation is available at:

```text
http://127.0.0.1:8000/redoc
```

---

## Use the dashboard

The dashboard contains the following sections:

1. Emissions summary.
2. Scope 1, Scope 2, and Scope 3 breakdown.
3. Document upload.
4. Manual carbon calculation.
5. AI ESG analysis.
6. Audit and evidence trail.

After uploading a document or completing a verified manual calculation, use the **Refresh** button if the dashboard does not update automatically.

---

## Upload a CSV file

### Required CSV columns

CSV files must contain these column names:

```csv
activity,quantity,unit
```

Example:

```csv
activity,quantity,unit
Electricity,1500,kWh
Diesel,500,L
Petrol,200,L
Air Travel,1200,km
Freight,5000,tonne-km
Natural Gas,800,kWh
```

### Upload steps

1. Open the dashboard at `http://127.0.0.1:8000/`.
2. Find **Upload ESG Document**.
3. Select a `.csv` file.
4. Click **Upload & Analyze**.
5. Review the upload result.
6. Check the **Audit & Evidence Trail** section.

A sample CSV is available at:

```text
sample_data\sample_esg_data.csv
```

The same sample data may also be available in the `uploads` folder.

### CSV behavior

For every complete row, the backend:

1. Classifies the activity.
2. Looks up the matching activity and unit.
3. Checks the factor status.
4. Calculates CO₂e only if the factor is marked `OFFICIAL`.
5. Saves the processing result to the audit database.

Rows with missing fields are skipped by the current MVP. Invalid or unsupported rows may be marked `UNVERIFIED`.

---

## Upload a PDF file

The current PDF extractor works best with text-based invoices that contain:

- An activity name.
- A numeric quantity.
- A recognized unit.

The current prototype recognizes these activities:

- Electricity
- Diesel
- Petrol

The current quantity patterns include:

- `1500 kWh`
- `500 litres`
- `500 L`

### Upload steps

1. Open the dashboard at `http://127.0.0.1:8000/`.
2. Find **Upload ESG Document**.
3. Select a `.pdf` file.
4. Click **Upload & Analyze**.
5. Review the extraction result.
6. Check the audit trail.

A sample PDF may be available at:

```text
uploads\sample_esg_electricity_invoice.pdf
```

### PDF limitations

The current extractor does not yet provide full invoice processing. It may not reliably handle:

- Scanned PDFs.
- Image-only documents.
- Multiple line items.
- Complex tables.
- MWh or other unsupported units.
- Missing or ambiguous quantities.
- Supplier and billing-period extraction.

A PDF that cannot be read or interpreted is returned as `UNVERIFIED` or an error and requires manual review.

---

## Perform a manual calculation

Use the **Manual Carbon Calculation** section.

Enter:

- Activity, for example `Electricity`
- Quantity, for example `1500`
- Unit, for example `kWh`

Then click **Calculate**.

The backend uses the following process:

```text
Activity
  → Scope classification
  → Emission-factor lookup
  → Verification-status check
  → Deterministic calculation
  → Audit-log entry
```

A successful calculation displays:

- Activity.
- Scope.
- Quantity and unit.
- Emission factor.
- Factor source.
- Factor year.
- CO₂e result.
- Calculation formula.

---

## Demo-only emission factors

The current file is:

```text
backend\data\emission_factors.csv
```

The included rows are marked:

```text
DEMO
```

This means they are examples for development and testing only.

The backend intentionally does **not** treat these factors as official. Known activities with demo factors are returned as:

```text
REVIEW_REQUIRED
```

and their calculated emissions are set to zero in the audit trail until the factor is verified.

Therefore, it is expected that:

- Manual calculations may return `400` with an unverified-factor message.
- CSV uploads may complete processing but show review-required records.
- The dashboard may show zero verified emissions.
- The audit trail may contain records with `REVIEW_REQUIRED`.
- Results must not be used for regulatory, financial, or sustainability disclosures.

Before using this application for real ESG reporting, replace the demo data with an approved and governed emission-factor dataset. The replacement data should include appropriate source documentation, geography, reporting year, methodology, unit definitions, and approval status.

---

## Status meanings

### `VERIFIED`

An approved factor was found and the deterministic calculation was completed.

### `REVIEW_REQUIRED`

A factor was found, but it is marked as demo, provisional, or otherwise not approved for official reporting.

### `UNVERIFIED`

The activity, quantity, unit, document extraction, or emission factor could not be reliably verified.

### `ERROR`

The request could not be processed, for example because a file could not be read.

---

## Audit trail

The **Audit & Evidence Trail** section displays records stored in:

```text
backend\esg_audit.db
```

Each record may include:

- Activity.
- Scope.
- Quantity.
- Unit.
- Emission factor.
- Factor source.
- Factor year.
- CO₂e amount.
- Calculation formula.
- Processing status.
- Source filename.
- Creation timestamp.

The audit database is initialized automatically when the FastAPI application starts.

Do not manually edit the database while the application is running.

---

## AI ESG analysis

The **AI ESG Compliance Analysis** section sends the activity details to the configured Lyzr agent.

The agent is instructed to:

- Use the deterministic scope classifier.
- Use the deterministic emission-factor lookup.
- Avoid inventing emission factors.
- Identify demo and unverified factors.
- Explain the calculation formula when applicable.
- State when review is required.

AI output is advisory. It does not replace:

- Emission-factor approval.
- Human review.
- Evidence verification.
- Regulatory interpretation.
- Formal ESG reporting controls.

If the AI section fails, check that:

1. The virtual environment is active.
2. `lyzr-adk` is installed.
3. `LYZR_API_KEY` is set.
4. The API key is valid.
5. The FastAPI process was restarted after changing `.env`.

---

## Troubleshooting

### `ModuleNotFoundError`

Confirm that the virtual environment is active:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then reinstall dependencies:

```powershell
python -m pip install fastapi "uvicorn[standard]" python-multipart pypdf python-dotenv lyzr-adk
```

### PowerShell refuses to activate the virtual environment

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then run:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Port 8000 is already in use

Start the application on another port:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

Then open:

```text
http://127.0.0.1:8001/
```

### The dashboard is blank or does not load data

Check that:

- The FastAPI terminal is still running.
- The browser URL uses `http://127.0.0.1:8000/`.
- The browser developer console does not show connection errors.
- The backend was started from the project root.

### A calculation says that review is required

This is expected with the current data because the factors in `backend/data/emission_factors.csv` are marked `DEMO`.

### A PDF cannot be processed

Confirm that the PDF:

- Contains selectable text.
- Contains a recognized activity.
- Contains a numeric quantity.
- Uses a recognized unit such as `kWh`, `L`, or `litres`.

---

## Current MVP limitations

The current project does not yet include:

- Production-approved emission factors.
- OCR for scanned PDFs.
- Full Excel processing.
- Complete GHG Protocol Scope 3 categorization.
- User authentication or authorization.
- Multi-organization support.
- Human review and approval workflows.
- Regulatory framework mappings.
- Report export.
- Historical reporting periods.
- Production database migrations.
- Automated tests.
- Production deployment configuration.

Treat all current outputs as development results requiring review.
