import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { gw, mw, shortDate, signedGw } from './format.js'
import Stat from './Stat.jsx'

const tooltipStyle = { background: 'var(--card)', border: '1px solid var(--border)' }

export default function Accuracy({ accuracy, selected, onSelectDay }) {
  const m = accuracy.metrics
  const buffer = accuracy.shortfallBuffer
  const histogram = accuracy.histogram.map((b) => ({ ...b, label: `${b.from / 1000}` }))
  return (
    <section className="card">
      <h2>How accurate is the forecast you buy on?</h2>
      <p className="sub">
        All {accuracy.days} delivery days, {m.count} hourly points, decision at {accuracy.decision} the day before.
      </p>

      <div className="stats">
        <Stat label="Mean abs. error" value={gw(m.mae)} note={`${m.maePct}% of mean actual (${gw(m.meanActual)})`} />
        <Stat label="Bias" value={signedGw(m.bias)} note={m.bias > 0 ? 'forecast too high on average' : 'forecast too low on average'} />
        <Stat label="90% of hours within" value={gw(m.p90Abs)} note={`median ${gw(m.p50Abs)}, worst ${gw(m.maxAbs)}`} />
        <Stat label="Safety margin (P90)" value={gw(buffer['90'])}
          note={`wind delivered at least forecast − ${gw(buffer['90'])} in 90% of hours`} />
      </div>

      <div className="callout">
        <strong>What it means for buying:</strong> if you plan with the forecast as-is, wind under-delivered by more
        than {gw(buffer['80'])} in 1 hour out of 5, and by more than {gw(buffer['95'])} in 1 hour out of 20. Wind
        alone was above {gw(accuracy.actualPercentiles['10'])} in 90% of half hours this month.
      </div>

      <div className="grid2">
        <div>
          <h3>Error distribution</h3>
          <p className="hint">Forecast − actual, GW. Right of zero means wind came in lower than forecast.</p>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={histogram} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis dataKey="label" stroke="var(--muted)" fontSize={12} />
              <YAxis stroke="var(--muted)" fontSize={12} width={40} />
              <Tooltip contentStyle={tooltipStyle}
                labelFormatter={(_, p) => p[0] && `${mw(p[0].payload.from)} to ${mw(p[0].payload.to)}`}
                formatter={(v) => [`${v} hours`, 'count']} />
              <Bar isAnimationActive={false} dataKey="count">
                {histogram.map((b) => <Cell key={b.from} fill={b.from >= 0 ? 'var(--forecast)' : 'var(--actual)'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div>
          <h3>Mean abs. error by hour of delivery</h3>
          <p className="hint">UK time of day. Later hours are forecast further ahead.</p>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={accuracy.byHour} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis dataKey="hour" stroke="var(--muted)" fontSize={12} />
              <YAxis tickFormatter={(v) => v / 1000} stroke="var(--muted)" fontSize={12} width={40} />
              <Tooltip contentStyle={tooltipStyle} labelFormatter={(h) => `${h}:00`} formatter={(v) => [mw(v), 'MAE']} />
              <Bar isAnimationActive={false} dataKey="mae" fill="var(--actual)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <h3>Mean abs. error by delivery day</h3>
      <p className="hint">Click a bar to open that day above.</p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={accuracy.byDay} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
          onClick={(e) => e?.activeLabel && onSelectDay(e.activeLabel)}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="date" tickFormatter={shortDate} stroke="var(--muted)" fontSize={12} interval={2} />
          <YAxis tickFormatter={(v) => v / 1000} stroke="var(--muted)" fontSize={12} width={40} />
          <Tooltip contentStyle={tooltipStyle} labelFormatter={shortDate}
            formatter={(v, name) => [mw(v), name === 'mae' ? 'MAE' : 'Bias']} />
          <Bar isAnimationActive={false} dataKey="mae" cursor="pointer">
            {accuracy.byDay.map((d) => (
              <Cell key={d.date} fill={d.date === selected ? 'var(--forecast)' : 'var(--actual)'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  )
}
