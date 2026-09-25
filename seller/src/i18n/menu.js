/** Seller menu / route label resolution. */

export const SELLER_ROUTE_I18N_KEYS = {
  '/dashboard': 'seller.dashboard',
  '/products': 'seller.menuProductList',
  '/products/categories': 'seller.menuCategories',
  '/products/brands': 'seller.menuBrands',
  '/promotions/seckill': 'seller.menuSeckill',
  '/promotions/groupbuy': 'seller.menuGroupBuy',
  '/promotions/coupon': 'seller.menuCoupon',
  '/promotions/tags': 'seller.menuPromoTags',
  '/orders': 'seller.menuOrderList',
  '/orders/refunds': 'seller.menuRefunds',
  '/orders/logistics': 'seller.menuLogistics',
  '/customers': 'seller.customers',
  '/chat': 'seller.chat',
  '/settings/profile': 'seller.menuProfile',
  '/settings/shop-rating': 'seller.menuShopRating',
  '/settings/closure': 'closure.title',
  '/settings/logistics': 'seller.menuLogisticsSettings',
  '/settings/payment': 'seller.menuPaymentSettings',
  '/staff': 'seller.staff',
}

export function resolveMenuLabel(t, te, path, fallbackTitle = '') {
  if (!path) return fallbackTitle
  const normalized = path === '/' ? '/dashboard' : path.replace(/\/$/, '')
  const key = SELLER_ROUTE_I18N_KEYS[normalized]
  if (key && te(key)) return t(key)
  return fallbackTitle || path
}
