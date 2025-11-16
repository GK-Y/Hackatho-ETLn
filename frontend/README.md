# Hackathon Frontend

Frontend for Dynamic ETL Pipeline (Vite + React)

## Prereqs
- Node 18+
- Backend running at http://127.0.0.1:8000
- Mongo (docker container named `mongo-hackathon`) started

## Start (PowerShell)
cd C:\Hackathon\frontend
npm install
npm run dev

Open the Vite URL (usually http://127.0.0.1:5173)

## Run the pytest upload harness
cd C:\Hackathon\hackathon_etl_v2
.\venv\Scripts\Activate.ps1
pip install pytest requests
pytest -q

## Demo steps
1. Ensure backend and Mongo are running.
2. Start frontend: `npm run dev`
3. Open the app and walk through Dashboard → Sources → Visualize → Records.
4. Use Demo mode for offline testing: `/demo`
