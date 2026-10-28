import { CartesianGrid, Legend, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { gw, mw } from './format.js'

export default function Horizon({ horizon }) {
  const first = horizon[0]
  const dayAhead = horizon.find((h) => h.hours === 24)
  return (
    <section className="card">
      <h2>Does the forecast get better closer to delivery?</h2>
      <p className="sub">
        Error of the latest forecast published at least N hours before each target time, all of January.
        A 1-hour-ahead forecast is off by {gw(first.mae)} on average; 24 hours ahead it is {gw(dayAhead.mae)}.
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={horizon} margin={{ top: 8, right: 16, left: 0, bottom: 16 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          {/* a 09:50 day-ahead decision covers targets 14 to 38 hours ahead */}
          <ReferenceArea x1={14} x2={38} fill="#e07b1f" fillOpacity={0.1}
            label={{ value: 'day-ahead decision range', position: 'insideTop', fill: 'var(--muted)', fontSize: 12 }} />
          <XAxis dataKey="hours" stroke="var(--muted)" fontSize={12}
            label={{ value: 'hours before target time', position: 'insideBottom', offset: -8, fill: 'var(--muted)', fontSize: 12 }} />
          <YAxis tickFormatter={(v) => v / 1000} stroke="var(--muted)" fontSize={12} width={40} />
          <Tooltip contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)' }}
            labelFormatter={(h) => `${h} hours ahead`} formatter={(v) => mw(v)} />
          <Legend verticalAlign="top" />
          <Line isAnimationActive={false} name="Mean abs. error" dataKey="mae" stroke="var(--actual)" strokeWidth={2} dot={false} />
          <Line isAnimationActive={false} name="Bias" dataKey="bias" stroke="var(--forecast)" strokeWidth={2} dot={false} />
          <Line isAnimationActive={false} name="P90 abs. error" dataKey="p90Abs" stroke="var(--muted)" strokeDasharray="4 4" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  )
}
