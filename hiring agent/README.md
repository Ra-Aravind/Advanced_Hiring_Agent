# AI Technical Assessment System

An advanced hiring platform where recruiters can generate technical assessments using natural language AI commands, generate candidate access codes, and automatically evaluate subjective answers using local AI (Ollama).

## Native Zero-Setup Stack
- **Frontend**: React 18, TypeScript, Vite, Tailwind-inspired Glassmorphism CSS
- **Backend**: FastAPI, SQLAlchemy (Async), **SQLite (zero-setup database)**
- **AI Integration**: Ollama using `tinyllama` (extremely lightweight, ~600MB)

## Prerequisites
1. **Python 3.10+** (for backend)
2. **Node.js 18+** (for frontend)
3. **Ollama** installed locally (for AI generation/evaluation)

---

### 1. Start Ollama (Local AI)
Make sure you have Ollama installed. Open a terminal and download/run the lightweight model:
```bash
ollama run tinyllama
```
*(Leave this terminal window running in the background).*

### 2. Start Backend & Database
Since we use SQLite, there is no database server to install. Just install the Python requirements and start the server:

Open a **new** terminal:
```powershell
cd "c:\Genvex_internship\hiring agent\backend"
# Optional: create a virtual environment first
# python -m venv venv
# .\venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
The backend API will be available at `http://localhost:8000`.
Swagger API Docs are at `http://localhost:8000/docs`.

### 3. Seed Initial Questions
Once the backend is running, open another terminal window and seed the database with 210 questions across 7 technologies:
```powershell
cd "c:\Genvex_internship\hiring agent\backend"
python -m seed_data.seed
```

### 4. Start Frontend
In a new terminal:
```powershell
cd "c:\Genvex_internship\hiring agent\frontend"
npm install
npm run dev
```
The frontend will be available at `http://localhost:5173`.

---

## Recruiter Workflow
1. Login with `admin@company.com` (password: `Admin@123`).
2. Navigate to Create Assessment and type a command like: *"Create a 20 question advanced Python assessment"*.
3. The AI parses this and sets up the test.
4. Generate an access code (e.g., `PY-A3KX9Z`) and share it with the candidate.

## Candidate Workflow
1. Go to the main landing page.
2. Enter the provided access code.
3. Complete the timed assessment (MCQ and Code snippets).
4. Upon submission, the AI immediately evaluates the code/subjective answers and generates a scorecard for the recruiter.
