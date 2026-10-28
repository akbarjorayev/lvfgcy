# Wind forecast monitor

A web app for a UK energy buyer who buys power on the day-ahead market. It answers two questions for January 2026:

1. **What wind forecast did I have when I had to decide?** For any delivery day it shows the latest national wind forecast published before the decision time (the day before), next to the actual wind generation.
2. **How much can I trust that forecast?** It measures the forecast error over the whole month: mean absolute error, bias, percentiles, the error by hour of day and by day, and a "safety margin": how much lower than the forecast wind came in 80/90/95/99% of the time. It also shows how the error grows with the forecast horizon.

Stack: React 19 + Vite + Recharts (front end), Python 3.12 + FastAPI (back end), Docker. Data comes from the Elexon BMRS API only: [FUELHH](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream) (actuals, `fuelType = WIND`) and [WINDFOR](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream) (forecasts).

Live app: **https://lvfgcy.vercel.app**

## How to run from scratch

### With Docker

```bash
git clone https://github.com/akbarjorayev/lvfgcy.git
cd lvfgcy
docker compose up --build    # http://localhost:8000
```

### Without Docker

Requirements: Python 3.12+ and Node.js 20+.

```bash
# API, port 8000
cd backend
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload

# web app, port 5173 (in another terminal; it proxies /api to port 8000)
cd frontend
npm install
npm run dev
```

Other commands:

```bash
cd backend && pytest                 # tests
cd backend && python -m app.elexon   # download the data again from Elexon (about 1 minute)
```

### Deploy to Vercel

The live app runs on Vercel (free Hobby plan): the React app is served as static files and the FastAPI app runs as a Python function (`api/index.py`, settings in `vercel.json`).

```bash
npx vercel login
npx vercel deploy --prod
```

The repo also has a `heroku.yml`, so the same Docker image can be deployed to Heroku (`heroku stack:set container`, then `git push heroku main`).

## How the numbers are calculated

- **Delivery days** are 2 Jan – 1 Feb 2026: decisions are made in January, one day before delivery. Days are UK local days (Europe/London), so clock changes are handled.
- **Decision time** defaults to 09:50 UK time on the day before delivery, the gate closure of the N2EX GB day-ahead auction. The user can change it in the app.
- **Forecast at decision**: for every target time, the latest WINDFOR forecast with `publishTime` at or before the decision moment. Nothing published after the decision is used. WINDFOR is published 8 times a day and has hourly values, so with a 09:50 decision the 09:30 forecast is used, 14–38 hours ahead of delivery.
- **Error** = forecast − actual, in MW. Positive means the wind came in lower than forecast, so the buyer is short. Actuals are half-hourly and forecasts are hourly, so errors are measured on the hour (24 points per day, 744 for the month).
- **Safety margin (P90)**: the 90th percentile of forecast − actual. Planning with "forecast − margin" covered the wind shortfall in 90% of hours in January.
- **Horizon chart**: for each N from 1 to 48 hours, the latest forecast published at least N hours before the target time.

### What January 2026 shows (09:50 decision)

- Mean absolute error is about **2.0 GW**, about 18% of mean wind output (11.3 GW).
- The forecast is **too high by 1.7 GW on average**. Most of the error is this bias, not random noise. One possible reason is that FUELHH is metered output after curtailment, while the forecast is not; this should be checked with the client.
- To be covered in 90% of hours, plan for about **4.2 GW less** wind than the forecast.
- A later forecast helps only a little: 1 hour ahead the error is still 1.7 GW, against about 1.9 GW 24 hours ahead.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/meta` | First and last delivery day, default decision time |
| GET | `/api/day?date=2026-01-15&decision=09:50` | Half-hourly actuals, forecast at decision, last forecast before delivery, daily metrics |
| GET | `/api/accuracy?decision=09:50` | Month metrics, safety margin, error histogram, error by hour and by day |
| GET | `/api/horizon` | Error by forecast horizon, 1–48 hours |

Errors come back with status 400 and `{ "detail": "..." }`. Interactive docs: `/docs`.

## Project structure

```
backend/
  app/
    main.py        FastAPI app: API routes, serves the built React app
    analysis.py    forecast selection and error metrics (the core logic)
    elexon.py      downloads FUELHH and WINDFOR from Elexon into data/
  data/            downloaded data (JSON), so the app starts without calling Elexon
  tests/           pytest: logic tests on small hand-made data, API tests on real data
  requirements.txt
frontend/
  src/
    App.jsx        page layout, controls, data loading
    DayView.jsx    one delivery day: chart and daily metrics
    Accuracy.jsx   month accuracy: metrics, histogram, error by hour and by day
    Horizon.jsx    error by forecast horizon
    Stat.jsx       metric tile
    api.js         API calls
    format.js      number and date formatting
api/index.py       Vercel entry point for the FastAPI app
vercel.json        Vercel build and routing settings
requirements.txt   Python packages for Vercel (same as backend/requirements.txt)
Dockerfile         builds the React app, then a Python image that serves API + app
docker-compose.yml local run with Docker
heroku.yml         Heroku container deploy (alternative)
```

## Use of AI tools

I used Claude (Anthropic) as a coding assistant while building this project: for writing parts of the code, tests and this README. I reviewed and checked the logic and the numbers.

## What I would improve with more time

1. **Probabilistic view.** Show a P10–P90 band around the forecast for each day, built from past errors by horizon and hour, instead of one number.
2. **Error by wind level.** Errors are larger when wind is ramping or high; split the metrics by forecast level and show ramp events.
3. **Live data.** Update the data from Elexon on a schedule and store it in a database (PostgreSQL), instead of a fixed January snapshot.
4. **Explain the bias.** Compare with curtailment data (BOALF) and embedded wind to find out why the forecast is too high, and offer a bias-corrected forecast.
5. **Production.** CI with tests and linting, front-end tests, caching headers, and splitting the chart library into a separate bundle.
