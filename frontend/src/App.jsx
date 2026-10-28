import { useEffect, useState } from 'react'
import { getAccuracy, getDay, getHorizon, getMeta } from './api.js'
import { addDays } from './format.js'
import DayView from './DayView.jsx'
import Accuracy from './Accuracy.jsx'
import Horizon from './Horizon.jsx'

export default function App() {
  const [meta, setMeta] = useState(null)
  const [date, setDate] = useState('2026-01-15')
  const [decision, setDecision] = useState('09:50')
  const [day, setDay] = useState(null)
  const [accuracy, setAccuracy] = useState(null)
  const [horizon, setHorizon] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getMeta().then((m) => { setMeta(m); setDecision(m.defaultDecision) }).catch((e) => setError(e.message))
    getHorizon().then(setHorizon).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!meta || !/^\d\d:\d\d$/.test(decision)) return
    getDay(date, decision).then(setDay).catch((e) => setError(e.message))
  }, [meta, date, decision])

  useEffect(() => {
    if (!meta || !/^\d\d:\d\d$/.test(decision)) return
    getAccuracy(decision).then(setAccuracy).catch((e) => setError(e.message))
  }, [meta, decision])

  const canGo = (n) => meta && addDays(date, n) >= meta.firstDay && addDays(date, n) <= meta.lastDay

  return (
    <div className="page">
      <header>
        <h1>Wind Forecast Monitor</h1>
        <p className="lead">
          GB national wind generation: the forecast you have at the day-ahead decision, and how far you can trust it.
          Delivery days 2 Jan – 1 Feb 2026 (decisions made in January). Data: Elexon BMRS FUELHH and WINDFOR.
        </p>
      </header>

      <section className="controls">
        <label>
          Delivery day
          <span className="row">
            <button onClick={() => setDate(addDays(date, -1))} disabled={!canGo(-1)} aria-label="Previous day">‹</button>
            <input
              type="date"
              value={date}
              min={meta?.firstDay}
              max={meta?.lastDay}
              onChange={(e) => e.target.value && setDate(e.target.value)}
            />
            <button onClick={() => setDate(addDays(date, 1))} disabled={!canGo(1)} aria-label="Next day">›</button>
          </span>
        </label>
        <label>
          Decision time (day before, UK)
          <input type="time" value={decision} onChange={(e) => setDecision(e.target.value)} />
        </label>
        <p className="hint">
          Default 09:50 is the N2EX day-ahead auction gate closure. The app only uses forecasts published before
          this moment.
        </p>
      </section>

      {error && <p className="error">Could not load data: {error}</p>}

      {day && <DayView day={day} />}
      {accuracy && <Accuracy accuracy={accuracy} selected={date} onSelectDay={setDate} />}
      {horizon && <Horizon horizon={horizon} />}

      <footer>
        Error = forecast − actual. Forecasts are hourly, actuals half-hourly, so errors are measured on the hour.
      </footer>
    </div>
  )
}
