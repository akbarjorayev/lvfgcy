const UK = 'Europe/London'

export const mw = (v) => (v == null ? '–' : `${Math.round(v).toLocaleString('en-GB')} MW`)
export const gw = (v) => (v == null ? '–' : `${(v / 1000).toFixed(1)} GW`)
export const signedGw = (v) => (v == null ? '–' : `${v > 0 ? '+' : ''}${(v / 1000).toFixed(1)} GW`)

export const hourMinute = (iso) =>
  new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: UK })

export const dayTime = (iso) =>
  new Date(iso).toLocaleString('en-GB', {
    weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: UK,
  })

export const shortDate = (isoDate) =>
  new Date(`${isoDate}T12:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })

export const longDate = (isoDate) =>
  new Date(`${isoDate}T12:00:00Z`).toLocaleDateString('en-GB', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })

export function addDays(isoDate, n) {
  const d = new Date(`${isoDate}T12:00:00Z`)
  d.setUTCDate(d.getUTCDate() + n)
  return d.toISOString().slice(0, 10)
}
