import { resolveImageUrl as resolveMediaUrl } from '@shared/utils/media.js'

export { resolveImageUrl } from '@shared/utils/media.js'

export function formatPrice(value) {
  const amount = Number(value)
  if (Number.isNaN(amount)) return '¥0.00'
  return `¥${amount.toFixed(2)}`
}

/** 合并主图与 gallery，去重后返回可访问 URL 列表 */
export function resolveProductImages(product) {
  if (!product) return []
  const raw = []
  if (product.image) raw.push(product.image)
  if (Array.isArray(product.gallery)) {
    product.gallery.forEach((item) => {
      if (item) raw.push(item)
    })
  }
  const seen = new Set()
  return raw
    .map((item) => resolveMediaUrl(item))
    .filter((item) => {
      if (!item || seen.has(item)) return false
      seen.add(item)
      return true
    })
}
