import regionTree from 'china-division/dist/pca-code.json'

let cachedAreaList = null
let cachedCascaderOptions = null

function buildAreaList() {
  const province_list = {}
  const city_list = {}
  const county_list = {}

  regionTree.forEach((province) => {
    province_list[province.code] = province.name
    province.children?.forEach((city) => {
      city_list[city.code] = city.name
      city.children?.forEach((district) => {
        county_list[district.code] = district.name
      })
    })
  })

  return { province_list, city_list, county_list }
}

function buildCascaderOptions() {
  return regionTree.map((province) => ({
    text: province.name,
    value: province.code,
    children: (province.children || []).map((city) => ({
      text: city.name,
      value: city.code,
      children: (city.children || []).map((district) => ({
        text: district.name,
        value: district.code,
      })),
    })),
  }))
}

export function getAreaList() {
  if (!cachedAreaList) {
    cachedAreaList = buildAreaList()
  }
  return cachedAreaList
}

export function getRegionCascaderOptions() {
  if (!cachedCascaderOptions) {
    cachedCascaderOptions = buildCascaderOptions()
  }
  return cachedCascaderOptions
}

export function findRegionCodes(province, city, district) {
  if (!province) return null
  const provinceNode = regionTree.find((item) => item.name === province)
  if (!provinceNode) return null
  const cityNode = provinceNode.children?.find((item) => item.name === city)
  if (!cityNode) return null
  const districtNode = cityNode.children?.find((item) => item.name === district)
  if (!districtNode) return null
  return {
    province,
    city,
    district,
    codes: [provinceNode.code, cityNode.code, districtNode.code],
  }
}

export function formatRegionText(province, city, district) {
  return [province, city, district].filter(Boolean).join(' / ')
}

export function maskPhone(phone) {
  const value = String(phone || '')
  if (value.length < 7) return value
  return `${value.slice(0, 3)}****${value.slice(-4)}`
}
