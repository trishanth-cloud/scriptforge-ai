# ScriptForge AI

> **Transform unstructured text, specs, and logs into intelligent, executable automation scripts with minimal human intervention.**

ScriptForge AI is a production-grade autonomous AI agent system that reads, understands, interprets, and analyzes unstructured text files, then automatically converts their contents into optimized, validated, and sandboxed executable scripts.

---

## 🌟 Key Features

- **Intelligent File Ingestion**: Ingests `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.log`, and `.yaml`/`.yml` files with automatic multi-encoding fallback (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`) and deep structured parsing.
- **AI Content Understanding**: Analyzes natural language instructions, detects required variables, identifies operational dependencies and ambiguities, and determines whether a task requires a script or automation pipeline.
- **Multi-Language Generation**: Automatically selects and generates clean, modular, and robust code for:
  - **Python**
  - **JavaScript**
  - **TypeScript**
  - **Bash**
  - **PowerShell**
  - **SQL**
  - **HTML/CSS**
- **Syntax Validation**: Multi-language static syntax validation (AST parsing for Python, brace balancing for JS/TS, SQL syntax heuristics, tag validation for HTML).
- **Controlled Sandboxed Execution**: Executes generated scripts in isolated subprocesses with CPU/time limits, output truncation limits, and in-memory SQLite for SQL.
- **Human-in-the-Loop Security**: Requires explicit user approval before executing scripts. Never executes raw user text as shell commands.
- **Self-Correction Engine**: When an execution produces a runtime error, ScriptForge captures `stderr`, diagnoses the issue, generates a revised script, re-validates, and re-executes (up to 3 automated attempts).
- **Modern Developer Dashboard**: Responsive Next.js 15 + Tailwind CSS dark-themed UI featuring Monaco code editor, real-time execution console, file previews, and task history.
- **Dual Mode (Gemini AI + Intelligent Fallback)**: Runs with live Gemini 2.0 Flash / Pro models when `GEMINI_API_KEY` is provided, and includes an intelligent template mock engine for offline testing.

---

## 🏗️ Architecture

```
scriptforge-ai/
├── backend/
│   ├── app/
│   │   ├── api/                     # FastAPI route handlers
│   │   │   ├── routes_files.py      # POST /upload, GET /{id}
│   │   │   ├── routes_tasks.py      # POST /, GET /, PUT /script, POST /regenerate
│   │   │   ├── routes_execution.py  # POST /execute, POST /validate
│   │   │   └── routes_results.py    # GET /download, GET /versions, GET /logs
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic schemas, enums, DTOs
│   │   ├── modules/
│   │   │   ├── file_ingestion.py    # Multi-format reader & encoding detector
│   │   │   ├── text_analysis.py     # AI text intent extractor
│   │   │   ├── task_classification.py # Automated task classifier
│   │   │   ├── planning.py          # Step-by-step execution planner
│   │   │   ├── script_generation.py # Production code generator
│   │   │   ├── code_validation.py   # Language-specific syntax validator
│   │   │   ├── sandbox_execution.py # Subprocess isolation executor
│   │   │   ├── error_correction.py  # Self-debugging engine (max 3 tries)
│   │   │   └── results_manager.py   # SQLite persistence & version history
│   │   ├── services/
│   │   │   ├── ai_engine.py         # Google Gemini SDK integration
│   │   │   └── pipeline.py          # Autonomous pipeline orchestrator
│   │   ├── config.py                # Environment configuration
│   │   ├── database.py              # SQLite schema & WAL connection manager
│   │   └── main.py                  # FastAPI application entry point
│   ├── tests/
│   │   ├── test_file_ingestion.py   # Ingestion unit tests
│   │   ├── test_validation.py       # Syntax validation tests
│   │   └── test_pipeline.py         # Full integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Dark theme layout with toast provider
│   │   │   ├── page.tsx             # Interactive dashboard
│   │   │   └── globals.css          # Tailwind & custom dev-tool styling
│   │   ├── components/
│   │   │   ├── Header.tsx           # Top navigation bar
│   │   │   ├── FileUpload.tsx       # Drag-and-drop file uploader
│   │   │   ├── FilePreview.tsx      # Raw content inspector
│   │   │   ├── AnalysisPanel.tsx    # AI insights & execution plan
│   │   │   ├── ScriptEditor.tsx     # Monaco code editor with download/edit
│   │   │   ├── ExecutionConsole.tsx # Real-time sandboxed terminal
│   │   │   └── ResultsPanel.tsx     # Outputs, debug reports, versions
│   │   ├── hooks/                   # Custom React hooks (useTask, useFileUpload, useExecution)
│   │   ├── lib/                     # Typed API client & interfaces
│   │   └── store/                   # Zustand global task store
│   └── package.json
└── README.md
```

---

## ⚡ Getting Started

### 1. Prerequisites
- **Python 3.11+** (Python 3.13 tested)
- **Node.js 18+** & **pnpm** (or npm)

### 2. Backend Setup

```bash
cd backend

# Create .env from example
copy .env.example .env

# Optional: Add your Gemini API key in backend/.env:
# GEMINI_API_KEY=your_gemini_api_key_here

# Install Python dependencies
pip install -r requirements.txt

# Run the test suite
pytest tests -v

# Start the FastAPI backend server (Port 8000)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be live at: `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

### 3. Frontend Setup

```bash
cd frontend

# Install frontend dependencies
pnpm install

# Start the Next.js development server
pnpm run dev
```

Frontend will be live at: `http://localhost:3000`.

---

## 🛡️ Security Model

1. **Untrusted Data Isolation**: All uploaded text files are treated as untrusted data inputs, never evaluated or executed directly.
2. **Explicit User Approval**: The execution endpoint (`/api/tasks/{task_id}/execute`) enforces `approved: true`. No script runs without user confirmation.
3. **Subprocess Isolation**: Generated scripts run inside dedicated child processes with execution timeouts (default: 30s) and working directory boundaries.
4. **Output Safeguards**: Standard output and error streams are truncated at 1MB to prevent memory exhaustion attacks.
5. **No Secret Leakage**: API keys and environment variables are strictly isolated to backend server settings and never forwarded to client responses.

---

## 🧪 Automated Test Results

The backend includes comprehensive test coverage:

```
tests/test_file_ingestion.py::test_validate_file_extensions PASSED       [ 10%]
tests/test_file_ingestion.py::test_validate_file_size PASSED             [ 20%]
tests/test_file_ingestion.py::test_get_file_preview PASSED               [ 30%]
tests/test_file_ingestion.py::test_ingest_json_file PASSED               [ 40%]
tests/test_file_ingestion.py::test_ingest_csv_file PASSED                [ 50%]
tests/test_pipeline.py::test_full_pipeline_flow PASSED                   [ 60%]
tests/test_validation.py::test_validate_python_valid PASSED              [ 70%]
tests/test_validation.py::test_validate_python_syntax_error PASSED       [ 80%]
tests/test_validation.py::test_validate_javascript_balanced_braces PASSED [ 90%]
tests/test_validation.py::test_validate_sql_syntax PASSED                [100%]

============================= 10 passed in 0.76s ==============================
```

Frontend build verification:
```
✓ Compiled successfully in 20.7s
✓ Linting and checking validity of types
✓ Generating static pages (4/4)
✓ Finalizing page optimization
```
