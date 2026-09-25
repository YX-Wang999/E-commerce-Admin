import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn } from '@/utils/auth'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/apply',
    name: 'Apply',
    component: () => import('@/views/apply/ApplyView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/components/layout/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: { name: 'Dashboard' } },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { titleKey: 'seller.dashboard' },
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/views/products/List.vue'),
        meta: { titleKey: 'seller.menuProductList' },
      },
      {
        path: 'products/categories',
        name: 'ProductCategories',
        component: () => import('@/views/products/Categories.vue'),
        meta: { titleKey: 'seller.menuCategories' },
      },
      {
        path: 'products/brands',
        name: 'ProductBrands',
        component: () => import('@/views/products/Brands.vue'),
        meta: { titleKey: 'seller.menuBrands' },
      },
      {
        path: 'promotions/seckill',
        name: 'PromotionSeckill',
        component: () => import('@/views/promotion/SeckillList.vue'),
        meta: { titleKey: 'seller.menuSeckill' },
      },
      {
        path: 'promotions/groupbuy',
        name: 'PromotionGroupBuy',
        component: () => import('@/views/promotion/GroupBuyList.vue'),
        meta: { titleKey: 'seller.menuGroupBuy' },
      },
      {
        path: 'promotions/coupon',
        name: 'PromotionCoupon',
        component: () => import('@/views/promotion/CouponList.vue'),
        meta: { titleKey: 'seller.menuCoupon' },
      },
      {
        path: 'subsidy',
        name: 'SubsidyApply',
        component: () => import('@/views/subsidy/ApplyView.vue'),
        meta: { titleKey: 'seller.subsidyTitle' },
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('@/views/orders/List.vue'),
        meta: { titleKey: 'seller.menuOrderList' },
      },
      {
        path: 'orders/refunds',
        name: 'OrderRefunds',
        component: () => import('@/views/orders/Refunds.vue'),
        meta: { titleKey: 'seller.menuRefunds' },
      },
      {
        path: 'orders/refunds/:id',
        name: 'RefundDetail',
        component: () => import('@/views/complaints/Detail.vue'),
        meta: { titleKey: 'seller.complaintDetail' },
      },
      {
        path: 'orders/logistics',
        name: 'OrderLogistics',
        component: () => import('@/views/orders/Logistics.vue'),
        meta: { titleKey: 'seller.menuLogistics' },
      },
      {
        path: 'orders/:id',
        name: 'OrderDetail',
        component: () => import('@/views/orders/Detail.vue'),
        meta: { titleKey: 'seller.orderDetail' },
      },
      {
        path: 'customers',
        name: 'Customers',
        component: () => import('@/views/customers/List.vue'),
        meta: { titleKey: 'seller.customers' },
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/chat/Workbench.vue'),
        meta: { titleKey: 'seller.chat' },
      },
      {
        path: 'points/rule',
        name: 'SellerPointsRule',
        component: () => import('@/views/points/RuleSettings.vue'),
        meta: { titleKey: 'sellerPoints.menuRule' },
      },
      {
        path: 'points/accounts',
        name: 'SellerPointsAccounts',
        component: () => import('@/views/points/Accounts.vue'),
        meta: { titleKey: 'sellerPoints.menuAccounts' },
      },
      {
        path: 'points/transactions',
        name: 'SellerPointsTransactions',
        component: () => import('@/views/points/Transactions.vue'),
        meta: { titleKey: 'sellerPoints.menuTransactions' },
      },
      {
        path: 'promotions/tags',
        name: 'PromoTags',
        component: () => import('@/views/promotions/TagManageView.vue'),
        meta: { titleKey: 'seller.promoTagsTitle' },
      },
      {
        path: 'settings/profile',
        name: 'SettingsProfile',
        component: () => import('@/views/settings/Profile.vue'),
        meta: { titleKey: 'seller.menuProfile' },
      },
      {
        path: 'settings/shop-rating',
        name: 'SettingsShopRating',
        component: () => import('@/views/settings/ShopRatingView.vue'),
        meta: { titleKey: 'seller.menuShopRating' },
      },
      {
        path: 'settings/closure',
        name: 'SettingsClosure',
        component: () => import('@/views/settings/ClosureView.vue'),
        meta: { titleKey: 'closure.title' },
      },
      {
        path: 'settings/logistics',
        name: 'SettingsLogistics',
        component: () => import('@/views/settings/Logistics.vue'),
        meta: { titleKey: 'seller.menuLogisticsSettings' },
      },
      {
        path: 'settings/payment',
        name: 'SettingsPayment',
        component: () => import('@/views/settings/Payment.vue'),
        meta: { titleKey: 'seller.menuPaymentSettings' },
      },
      {
        path: 'staff',
        name: 'Staff',
        component: () => import('@/views/settings/Staff.vue'),
        meta: { titleKey: 'seller.staff' },
      },
      { path: 'complaints', redirect: { name: 'OrderRefunds' } },
      { path: 'complaints/:id', redirect: (to) => ({ name: 'RefundDetail', params: { id: to.params.id } }) },
      { path: 'settings', redirect: { name: 'SettingsProfile' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) {
    if (to.name === 'Login' && isLoggedIn()) {
      return { path: '/dashboard' }
    }
    return true
  }

  if (!isLoggedIn()) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const authStore = useAuthStore()
  if (!authStore.user) {
    try {
      await authStore.fetchProfile()
    } catch {
      authStore.logout()
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }
  return true
})

export default router
