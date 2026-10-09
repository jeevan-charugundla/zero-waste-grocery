# Zero-Waste Grocery — Agentic AI Starter

Starter scaffold for the GDGoC HITAM PS2 hackathon problem: perishable demand, shelf-life/spoilage risk, explainable recommendations, planner approval, simulated POS/ERP/WMS, and four add-ons (bundles, manager copilot, donation/disposal, consent-aware customer targeting).

## Stack
- Frontend: React, TypeScript, Vite, Tailwind CSS, Recharts, Supabase JS
- Backend: Python, FastAPI, Groq SDK, Pandas, scikit-learn
- Data: Supabase PostgreSQL, Auth, RLS
- Deployment later: Vercel + Python API host

## Requirements
Node.js 20.19+ or 22.12+, Python 3.11+, Git, Supabase project, Groq API key.

## Frontend
```bash
cd frontend
npm install
npm install @supabase/supabase-js recharts lucide-react
npm install -D tailwindcss @tailwindcss/vite
npx shadcn@latest init
npx shadcn@latest add button card badge table tabs input dialog dropdown-menu
cp .env.example .env.local
npm run dev
```
On Windows PowerShell use `Copy-Item .env.example .env.local` instead of `cp`.
Follow the current shadcn Vite prompts if its CLI differs.

## Backend
```bash
cd backend
python -m venv .venv
```
Windows: ` .\.venv\Scripts\Activate.ps1 `; macOS/Linux: `source .venv/bin/activate`.
```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
Health: http://127.0.0.1:8000/health · API docs: http://127.0.0.1:8000/docs

## Supabase
Open Supabase SQL Editor and run `supabase/migrations/0001_initial_schema.sql`. Review and tighten RLS before any real customer data or multi-store deployment.

## Secrets
Frontend `.env.local` may contain only `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_BASE_URL`. Backend `.env` contains `GROQ_API_KEY`, `SUPABASE_URL`, and optional server-only Supabase service key. Never use `VITE_` for Groq/service-role secrets. Never commit `.env` files.

## Build order
1. Start frontend/API and configure Supabase.
2. Seed demo stores/products/batches.
3. Implement inventory movements and server-side inventory queries.
4. Implement moving-average forecast and spoilage heuristic.
5. Build specialist agent proposals + orchestrator + planner approval.
6. Add bundles, consent-checked simulated campaigns, copilot and donation/disposal.
7. Compare agent results against baseline forecasting/rules.

## Safety/data rules
Inventory must be tracked by batch and expiry; barcode alone may not identify a batch expiry. Every receipt, sale, transfer, waste, donation and correction needs a stock movement/audit trail. Expired/unsafe food must not be donated for consumption. Customer targeting must check channel/purpose consent and opt-outs. AI proposals require manager approval. Use server-side queried data to ground Groq answers; never trust client-provided stock facts. Label heuristic confidence honestly.
