# UK Wind Forecast Monitor

A web app that helps a UK energy trading team understand the wind generation forecast available at decision time for the day-ahead market, and measure how accurate those forecasts are. Covers purchase decisions made in January 2026.

**Live app:** https://gridbricks-project-kappa.vercel.app

## What it does

- Pick a date range and a forecast horizon (0 to 42 hours before delivery)
- For every half hour, the app shows actual national wind generation next to the latest forecast that was published at least that many hours before delivery. Forecasts published after that cutoff are excluded, because the trader would not have had them yet
- Error metrics for the selected window: MAE, RMSE, bias, P90 absolute error, and MAE as a % of output
- A chart showing how forecast error grows as the horizon gets longer

Data comes from Elexon BMRS: `FUELHH` (filtered to `WIND`) for actuals, `WINDFOR` for forecasts.

## Key findings (January 2026)

- At 4 hours ahead, the forecast misses by about 1,700 MW on average, and 9 times out of 10 the miss is under about 3,600 MW
- At 24 hours ahead, the average miss grows to about 1,900 MW, with 9 in 10 misses under about 3,850 MW
- Error stays fairly flat up to around 18 hours ahead, then rises more steeply
- Forecasts ran higher than actual generation on average, so relying on them as-is would lead to under-buying

## Project structure

```
api/
  index.py           Vercel entry point, loads the FastAPI app from backend/
backend/
  data/              January 2026 actuals and forecasts pulled from Elexon (JSON)
  fetch_data.py      One-off script that downloads the data from the Elexon API
  logic.py           Core logic: forecast selection at a given horizon, error metrics
  main.py            FastAPI app exposing /api/series and /api/horizon-curve
  test_logic.py      Unit tests for the forecast selection rule
  Dockerfile
  requirements.txt
frontend/
  src/App.jsx        Dashboard: controls, metric cards, charts (React + Recharts)
  src/App.css        Styles
  nginx.conf         Serves the build and proxies /api to the backend in Docker
  Dockerfile
docker-compose.yml   Runs backend and frontend together
vercel.json          Vercel build and routing config
requirements.txt     Python dependencies for the Vercel function
```

## Running it

### With Docker

```bash
docker compose up --build
```

Then open http://localhost:3000

### Without Docker

Backend:

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend (in a second terminal):

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173

### Tests

```bash
cd backend
pytest
```

### Refreshing the data

```bash
cd backend
python fetch_data.py
```

## API

- `GET /api/series?start=2026-01-02&end=2026-01-08&horizon=4` returns actual vs forecast points and error metrics for the range
- `GET /api/horizon-curve?start=2026-01-02&end=2026-02-01` returns MAE and P90 error at each horizon
- Interactive API docs at `/docs` when running locally

## Key design choices

- **Forecast selection:** for each target time, take the newest forecast published at or before `target - horizon`, and ignore anything older than 48 hours. Binary search keeps it fast
- **Static data:** the analysis period is fixed, so the data is pulled once and stored as JSON instead of calling Elexon on every request. Keeps the app fast and avoids API rate limits
- **Only matched points count:** forecasts are hourly and actuals are half-hourly, so error metrics are calculated only where both exist
- **Horizon capped at 42h:** that's the furthest ahead the WINDFOR forecasts reach in this data
- **Timezone:** all times are UTC, which equals UK time in January (GMT)
- **Logic separate from API:** `logic.py` has no web code in it, so it can be tested on its own

## What I'd do next

- Scheduled ingestion into a database so the app works on live data
- Add demand forecasts to show the residual power that needs buying
- Look into curtailment as a possible reason forecasts run higher than actual output
- CI to run tests on every push

## AI tools

I used Claude (Anthropic) as an assistant while building this project, for guidance on structure, code, and deployment.
