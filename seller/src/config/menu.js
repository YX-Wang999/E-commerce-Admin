/** Seller sidebar menu — top-level items with mixed expand / direct link. */

export const SELLER_MENU_ITEMS = [
  {
    path: '/dashboard',
    icon: 'Odometer',
    labelKey: 'seller.dashboard',
    children: null,
  },
  {
    icon: 'Goods',
    labelKey: 'seller.products',
    groupKey: 'products',
    children: [
      { path: '/products', labelKey: 'seller.menuProductList' },
      { path: '/products/categories', labelKey: 'seller.menuCategories' },
      { path: '/products/brands', labelKey: 'seller.menuBrands' },
    ],
  },
  {
    icon: 'List',
    labelKey: 'seller.orders',
    groupKey: 'orders',
    children: [
      { path: '/orders', labelKey: 'seller.menuOrderList' },
      { path: '/orders/refunds', labelKey: 'seller.menuRefunds', badgePath: '/orders/refunds' },
      { path: '/orders/logistics', labelKey: 'seller.menuLogistics' },
    ],
  },
  {
    icon: 'Ticket',
    labelKey: 'seller.promotions',
    groupKey: 'promotions',
    children: [
      { path: '/promotions/seckill', labelKey: 'seller.menuSeckill' },
      { path: '/promotions/groupbuy', labelKey: 'seller.menuGroupBuy' },
      { path: '/promotions/coupon', labelKey: 'seller.menuCoupon' },
      { path: '/promotions/tags', labelKey: 'seller.menuPromoTags' },
    ],
  },
  {
    path: '/subsidy',
    icon: 'Medal',
    labelKey: 'seller.subsidyFilingTitle',
    children: null,
  },
  {
    path: '/customers',
    icon: 'User',
    labelKey: 'seller.customers',
    children: null,
  },
  {
    path: '/chat',
    icon: 'ChatDotRound',
    labelKey: 'seller.chat',
    children: null,
    badgePath: '/chat',
  },
  {
    icon: 'Coin',
    labelKey: 'sellerPoints.menuTitle',
    groupKey: 'points',
    children: [
      { path: '/points/rule', labelKey: 'sellerPoints.menuRule' },
      { path: '/points/accounts', labelKey: 'sellerPoints.menuAccounts' },
      { path: '/points/transactions', labelKey: 'sellerPoints.menuTransactions' },
    ],
  },
  {
    icon: 'Setting',
    labelKey: 'seller.settings',
    groupKey: 'settings',
    children: [
      { path: '/settings/profile', labelKey: 'seller.menuProfile' },
      { path: '/settings/shop-rating', labelKey: 'seller.menuShopRating' },
      { path: '/settings/closure', labelKey: 'closure.title' },
      { path: '/settings/logistics', labelKey: 'seller.menuLogisticsSettings' },
      { path: '/settings/payment', labelKey: 'seller.menuPaymentSettings' },
    ],
  },
  {
    path: '/staff',
    icon: 'UserFilled',
    labelKey: 'seller.staff',
    children: null,
  },
]

export const SELLER_EXPANDED_STORAGE_KEY = 'seller-menu-expanded'
