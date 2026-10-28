async function get(path, params = {}) {
  const res = await fetch(`/api/${path}?${new URLSearchParams(params)}`)
  const body = await res.json()
  if (!res.ok) throw new Error(body.detail || res.statusText)
  return body
}

export const getMeta = () => get('meta')
export const getDay = (date, decision) => get('day', { date, decision })
export const getAccuracy = (decision) => get('accuracy', { decision })
export const getHorizon = () => get('horizon')
