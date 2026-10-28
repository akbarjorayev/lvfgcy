import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { dayTime, gw, hourMinute, longDate, mw, signedGw } from './format.js'
import Stat from './Stat.jsx'

export default function DayView({ day }) {
  const m = day.metrics
  const published = day.forecastPublishTimes
  return (
    <section className="card">
      <h2>{longDate(day.date)}</h2>
      <p className="sub">
        Decision at {dayTime(day.decisionTime)}.{' '}
        {published.length
          ? `Using the forecast published ${published.map(dayTime).join(', ')}.`
          : 'No forecast was published before this decision.'}
      </p>

      <div className="stats">
        <Stat label="Mean actual" value={gw(m.meanActual)} />
        <Stat label="Mean abs. error" value={gw(m.mae)} note={m.maePct != null ? `${m.maePct}% of actual` : null} />
        <Stat label="Bias" value={signedGw(m.bias)} note={m.bias > 0 ? 'forecast too high' : 'forecast too low'} />
        <Stat label="Worst hour" value={gw(m.maxAbs)} />
      </div>

      <div className="chart">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={day.rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="time" tickFormatter={hourMinute} interval={5} stroke="var(--muted)" fontSize={12} />
            <YAxis tickFormatter={(v) => `${v / 1000}`} stroke="var(--muted)" fontSize={12} width={40}
              label={{ value: 'GW', angle: -90, position: 'insideLeft', fill: 'var(--muted)', fontSize: 12 }} />
            <Tooltip
              labelFormatter={hourMinute}
              formatter={(v) => mw(v)}
              contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)' }}
            />
            <Legend />
            <Line isAnimationActive={false} name="Actual" dataKey="actual" stroke="var(--actual)" strokeWidth={2} dot={false} />
            <Line isAnimationActive={false} name="Forecast at decision" dataKey="forecast" stroke="var(--forecast)" strokeWidth={2}
              dot={false} connectNulls />
            <Line isAnimationActive={false} name="Last forecast before delivery" dataKey="latestForecast" stroke="var(--muted)"
              strokeDasharray="4 4" dot={false} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="hint">
        The dashed line is the most recent forecast before each half hour. You cannot use it for the day-ahead
        purchase, but it shows how much the forecast changed after you decided.
      </p>
    </section>
  )
}
