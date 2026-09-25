/** Resolve shop display name from a product payload. */
export function getProductShopName(product) {
  if (!product) return ''
  if (product.tenant?.name) return product.tenant.name
  return product.tenant_name || ''
}

/** Resolve shop id from a product payload. */
export function getProductShopId(product) {
  if (!product) return null
  if (product.tenant?.id) return product.tenant.id
  if (typeof product.tenant === 'number') return product.tenant
  return null
}

/** Resolve shop logo from a product payload. */
export function getProductShopLogo(product) {
  if (!product) return ''
  if (product.tenant?.logo) return product.tenant.logo
  return product.tenant_logo || ''
}

/** Whether product belongs to a merchant shop (not platform-owned). */
export function isMerchantProduct(product) {
  return Boolean(getProductShopId(product))
}
