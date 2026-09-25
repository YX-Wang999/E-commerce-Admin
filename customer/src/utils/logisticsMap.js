/** Preset coordinates for common cities (lng/lat for Baidu Map). */

export const CITY_COORDINATES = {
  北京: { lng: 116.404, lat: 39.915 },
  北京市: { lng: 116.404, lat: 39.915 },
  上海: { lng: 121.473, lat: 31.23 },
  上海市: { lng: 121.473, lat: 31.23 },
  广州: { lng: 113.264, lat: 23.13 },
  广州市: { lng: 113.264, lat: 23.13 },
  深圳: { lng: 114.057, lat: 22.543 },
  深圳市: { lng: 114.057, lat: 22.543 },
  杭州: { lng: 120.155, lat: 30.274 },
  杭州市: { lng: 120.155, lat: 30.274 },
  南京: { lng: 118.796, lat: 32.058 },
  南京市: { lng: 118.796, lat: 32.058 },
  武汉: { lng: 114.305, lat: 30.593 },
  武汉市: { lng: 114.305, lat: 30.593 },
  成都: { lng: 104.066, lat: 30.572 },
  成都市: { lng: 104.066, lat: 30.572 },
  重庆: { lng: 106.551, lat: 29.563 },
  重庆市: { lng: 106.551, lat: 29.563 },
  西安: { lng: 108.939, lat: 34.341 },
  西安市: { lng: 108.939, lat: 34.341 },
  天津: { lng: 117.201, lat: 39.084 },
  天津市: { lng: 117.201, lat: 39.084 },
  苏州: { lng: 120.585, lat: 31.299 },
  苏州市: { lng: 120.585, lat: 31.299 },
  郑州: { lng: 113.625, lat: 34.746 },
  郑州市: { lng: 113.625, lat: 34.746 },
  长沙: { lng: 112.938, lat: 28.228 },
  长沙市: { lng: 112.938, lat: 28.228 },
  东莞: { lng: 113.751, lat: 23.021 },
  东莞市: { lng: 113.751, lat: 23.021 },
  佛山: { lng: 113.122, lat: 23.028 },
  佛山市: { lng: 113.122, lat: 23.028 },
  宁波: { lng: 121.544, lat: 29.868 },
  宁波市: { lng: 121.544, lat: 29.868 },
  青岛: { lng: 120.382, lat: 36.067 },
  青岛市: { lng: 120.382, lat: 36.067 },
  沈阳: { lng: 123.431, lat: 41.805 },
  沈阳市: { lng: 123.431, lat: 41.805 },
  济南: { lng: 117.0, lat: 36.675 },
  济南市: { lng: 117.0, lat: 36.675 },
  合肥: { lng: 117.227, lat: 31.82 },
  合肥市: { lng: 117.227, lat: 31.82 },
  福州: { lng: 119.296, lat: 26.074 },
  福州市: { lng: 119.296, lat: 26.074 },
  厦门: { lng: 118.089, lat: 24.479 },
  厦门市: { lng: 118.089, lat: 24.479 },
  昆明: { lng: 102.832, lat: 24.88 },
  昆明市: { lng: 102.832, lat: 24.88 },
  无锡: { lng: 120.311, lat: 31.491 },
  无锡市: { lng: 120.311, lat: 31.491 },
  哈尔滨: { lng: 126.534, lat: 45.803 },
  哈尔滨市: { lng: 126.534, lat: 45.803 },
  大连: { lng: 121.614, lat: 38.914 },
  大连市: { lng: 121.614, lat: 38.914 },
  温州: { lng: 120.699, lat: 27.994 },
  温州市: { lng: 120.699, lat: 27.994 },
  石家庄: { lng: 114.514, lat: 38.042 },
  南昌市: { lng: 115.858, lat: 28.682 },
  南昌: { lng: 115.858, lat: 28.682 },
  长春: { lng: 125.323, lat: 43.817 },
  长春市: { lng: 125.323, lat: 43.817 },
  贵阳: { lng: 106.713, lat: 26.578 },
  贵阳市: { lng: 106.713, lat: 26.578 },
  南宁: { lng: 108.366, lat: 22.817 },
  南宁市: { lng: 108.366, lat: 22.817 },
  太原: { lng: 112.548, lat: 37.857 },
  太原市: { lng: 112.548, lat: 37.857 },
  乌鲁木齐: { lng: 87.616, lat: 43.825 },
  兰州市: { lng: 103.834, lat: 36.061 },
  兰州: { lng: 103.834, lat: 36.061 },
  海口: { lng: 110.331, lat: 20.031 },
  海口市: { lng: 110.331, lat: 20.031 },
  呼和浩特: { lng: 111.749, lat: 40.842 },
  银川市: { lng: 106.278, lat: 38.466 },
  西宁: { lng: 101.778, lat: 36.617 },
  西宁市: { lng: 101.778, lat: 36.617 },
  拉萨: { lng: 91.132, lat: 29.66 },
  拉萨市: { lng: 91.132, lat: 29.66 },
}

const CITY_PATTERN = /([\u4e00-\u9fff]{2,10}?市)/

export function extractCityFromText(text = '') {
  const match = String(text).match(CITY_PATTERN)
  return match ? match[1] : null
}

const DEFAULT_COORDINATE = { lng: 116.404, lat: 39.915 }

export function extractCityFromTrace(trace) {
  if (!trace) return null
  if (trace.city) {
    const city = String(trace.city).trim()
    return city.endsWith('市') ? city : `${city}市`
  }
  if (trace.area) {
    const fromArea = extractCityFromText(trace.area) || trace.area.trim()
    if (fromArea) return fromArea
  }
  const bracketMatch = String(trace.content || '').match(/【([\u4e00-\u9fff]{2,10}?市?)】/)
  if (bracketMatch) {
    const name = bracketMatch[1]
    return name.endsWith('市') ? name : `${name}市`
  }
  return extractCityFromText(trace.content)
}

export function resolveCityCoordinate(cityName, { fallback = true } = {}) {
  if (!cityName) return fallback ? { ...DEFAULT_COORDINATE } : null
  const trimmed = cityName.trim()
  const variants = [
    trimmed,
    trimmed.endsWith('市') ? trimmed.slice(0, -1) : `${trimmed}市`,
  ]
  for (const key of variants) {
    if (CITY_COORDINATES[key]) {
      return CITY_COORDINATES[key]
    }
  }
  if (fallback) {
    console.warn('[logisticsMap] 未知城市:', cityName, '使用默认坐标（北京）')
    return { ...DEFAULT_COORDINATE }
  }
  return null
}

function offsetDuplicatePosition(position, index) {
  if (index === 0) return position
  const offset = index * 0.08
  return { lng: position.lng + offset, lat: position.lat + offset * 0.5 }
}

/**
 * Convert logistics traces to map marker points (chronological, deduped by city).
 * @returns {Array<{ position: { lng: number, lat: number }, label: string, title: string, kind: 'start'|'middle'|'end' }>}
 */
export function tracesToMapPoints(traces = [], address = '') {
  if (!traces.length) return []

  const chronological = [...traces].reverse()
  const cityNodes = []

  for (const trace of chronological) {
    const city = extractCityFromTrace(trace)
    if (!city) continue
    const last = cityNodes[cityNodes.length - 1]
    if (last?.city === city) continue
    cityNodes.push({
      city,
      title: trace.content || city,
      time: trace.time || '',
    })
  }

  const destCity = extractCityFromText(address)
  const reachedDestStage = chronological.some((trace) =>
    ['transporting', 'delivering', 'delivered'].includes(trace.status),
  )
  if (reachedDestStage && destCity && cityNodes[cityNodes.length - 1]?.city !== destCity) {
    cityNodes.push({ city: destCity, title: destCity, time: '' })
  }

  const points = []
  const positionCounts = new Map()
  for (const node of cityNodes) {
    const basePosition = resolveCityCoordinate(node.city)
    const key = `${basePosition.lng},${basePosition.lat}`
    const duplicateIndex = positionCounts.get(key) || 0
    positionCounts.set(key, duplicateIndex + 1)
    const position = offsetDuplicatePosition(basePosition, duplicateIndex)
    points.push({
      position,
      label: node.city.replace(/市$/, ''),
      title: node.title,
      time: node.time,
    })
  }

  if (!points.length) return []

  return points.map((point, index) => ({
    ...point,
    kind: index === 0 ? 'start' : index === points.length - 1 ? 'end' : 'middle',
  }))
}
