import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { isLoggedIn } from '@/utils/auth'
import { getSessionReady } from '@/utils/sessionBootstrap'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { public: true },
    },
    {
      path: '/forgot-password',
      name: 'ForgotPassword',
      component: () => import('@/views/auth/ForgotPasswordView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/components/layout/MainLayout.vue'),
      children: [
        {
          path: '',
          name: 'Home',
          component: () => import('@/views/home/HomeView.vue'),
          meta: { guest: true, hideMobileTopBar: true },
        },
        {
          path: 'category',
          name: 'Category',
          component: () => import('@/views/category/CategoryView.vue'),
          meta: { guest: true },
        },
        {
          path: 'cart',
          name: 'Cart',
          component: () => import('@/views/cart/CartView.vue'),
          meta: { titleKey: 'header.cart', guest: true },
        },
        {
          path: 'checkout',
          name: 'Checkout',
          component: () => import('@/views/checkout/CheckoutView.vue'),
          meta: { titleKey: 'checkout.title', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'orders',
          name: 'OrderList',
          component: () => import('@/views/order/OrderListView.vue'),
          meta: { titleKey: 'order.listTitle', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'orders/:id',
          redirect: (to) => ({ name: 'OrderDetail', params: { id: to.params.id } }),
        },
        {
          path: 'order/:id',
          name: 'OrderDetail',
          component: () => import('@/views/order/OrderDetailView.vue'),
          meta: { titleKey: 'checkout.orderDetailTitle', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'complaints',
          name: 'ComplaintList',
          component: () => import('@/views/complaint/ComplaintListView.vue'),
          meta: { titleKey: 'complaint.myTitle', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'complaints/create',
          name: 'ComplaintCreate',
          component: () => import('@/views/complaint/ComplaintCreateView.vue'),
          meta: { titleKey: 'complaint.createTitle', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'complaints/:id',
          name: 'ComplaintDetail',
          component: () => import('@/views/complaint/ComplaintDetailView.vue'),
          meta: { titleKey: 'complaint.detailTitle', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'addresses',
          name: 'AddressManage',
          component: () => import('@/views/address/AddressManageView.vue'),
          meta: { titleKey: 'address.title', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('@/views/profile/ProfileView.vue'),
          meta: { titleKey: 'header.personalCenter', guest: true },
        },
        {
          path: 'membership/benefits',
          name: 'MembershipBenefits',
          component: () => import('@/views/membership/BenefitsView.vue'),
          meta: { titleKey: 'membership.benefitsTitle', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'notifications',
          name: 'Notifications',
          component: () => import('@/views/notification/NotificationListView.vue'),
          meta: { titleKey: 'notification.title', requiresAuth: true },
        },
        {
          path: 'search',
          name: 'Search',
          component: () => import('@/views/search/SearchView.vue'),
          meta: { guest: true },
        },
        {
          path: 'product/:id',
          name: 'ProductDetail',
          component: () => import('@/views/product/ProductDetailView.vue'),
          meta: { guest: true, hideMobileTopBar: true },
        },
        {
          path: 'coupons',
          name: 'CouponCenter',
          component: () => import('@/views/coupon/CouponCenter.vue'),
          meta: { titleKey: 'coupon.title', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'seckill',
          name: 'Seckill',
          component: () => import('@/views/seckill/SeckillList.vue'),
          meta: { titleKey: 'seckill.title', guest: true, plainLayout: true },
        },
        {
          path: 'points',
          name: 'PointsCenter',
          component: () => import('@/views/points/PointsCenter.vue'),
          meta: { titleKey: 'header.pointsCenter', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'points-mall',
          name: 'PointsMall',
          component: () => import('@/views/points/PointsMallView.vue'),
          meta: { titleKey: 'pointsMall.title', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'points-mall/orders',
          name: 'PointsMallOrders',
          component: () => import('@/views/points/PointsMallOrdersView.vue'),
          meta: { titleKey: 'pointsMall.ordersTitle', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'chat',
          name: 'Chat',
          component: () => import('@/views/chat/ChatView.vue'),
          meta: { titleKey: 'chat.title', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'reviews',
          name: 'ReviewCenter',
          component: () => import('@/views/review/ReviewCenterView.vue'),
          meta: { titleKey: 'review.centerTitle', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'reviews/:id',
          name: 'ReviewDetail',
          component: () => import('@/views/review/ReviewDetailView.vue'),
          meta: { titleKey: 'review.detailTitle', requiresAuth: false, plainLayout: true },
        },
        {
          path: 'product/:id/reviews',
          name: 'ProductReviews',
          component: () => import('@/views/review/ProductReviewListView.vue'),
          meta: { titleKey: 'review.listTitle', guest: true, plainLayout: true },
        },
        {
          path: 'suggestions',
          name: 'Suggestions',
          component: () => import('@/views/suggestion/SuggestionView.vue'),
          meta: { titleKey: 'suggestion.title', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'shop/:id',
          name: 'ShopHome',
          component: () => import('@/views/shop/ShopHomeView.vue'),
          meta: { titleKey: 'shop.title', guest: true, plainLayout: true },
        },
        {
          path: 'shops',
          name: 'ShopList',
          component: () => import('@/views/shop/ShopListView.vue'),
          meta: { titleKey: 'shop.listTitle', guest: true, plainLayout: true },
        },
        {
          path: 'profile/settings',
          name: 'Settings',
          component: () => import('@/views/profile/SettingsView.vue'),
          meta: { titleKey: 'settings.title', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'profile/edit',
          name: 'ProfileEdit',
          component: () => import('@/views/profile/ProfileEditView.vue'),
          meta: { titleKey: 'settings.personalInfo', requiresAuth: true, plainLayout: true },
        },
        {
          path: 'channel/billion-subsidy',
          name: 'BillionSubsidyChannel',
          component: () => import('@/views/channel/BillionSubsidyChannelView.vue'),
          meta: { titleKey: 'home.billionSubsidy', guest: true },
        },
        {
          path: 'channel/super-discount',
          name: 'SuperDiscountChannel',
          component: () => import('@/views/channel/SuperDiscountChannelView.vue'),
          meta: { titleKey: 'home.superDiscountTitle', guest: true },
        },
        {
          path: 'subsidy',
          name: 'Subsidy',
          component: () => import('@/views/subsidy/SubsidyListView.vue'),
          meta: { titleKey: 'subsidy.zoneTitle', guest: true },
        },
        {
          path: 'channel/subsidy',
          redirect: { name: 'Subsidy' },
        },
        {
          path: 'new-products',
          redirect: { name: 'Home', query: { channel: 'newArrival' } },
        },
        {
          path: 'channel/new',
          redirect: { name: 'Home', query: { channel: 'newArrival' } },
        },
        {
          path: 'channel/live',
          name: 'LiveChannel',
          component: () => import('@/views/channel/ChannelPlaceholderView.vue'),
          meta: { titleKey: 'home.liveStream', guest: true },
        },
        {
          path: 'channel/seckill',
          name: 'SeckillChannel',
          component: () => import('@/views/seckill/SeckillList.vue'),
          meta: { titleKey: 'home.flashSale', guest: true },
        },
        {
          path: 'channel/free-shipping',
          name: 'FreeShippingChannel',
          component: () => import('@/views/channel/ChannelPlaceholderView.vue'),
          meta: { titleKey: 'home.freeShipping', guest: true },
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  await getSessionReady()

  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  authStore.isLoggedIn = isLoggedIn()

  if (requiresAuth && !isLoggedIn()) {
    return {
      name: 'Profile',
      query: {
        redirect: to.fullPath,
        login: '1',
      },
      replace: true,
    }
  }

  if (to.path === '/login' && isLoggedIn()) {
    return '/'
  }
})

export default router
