import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn } from '@/utils/auth'
import { useAuthStore } from '@/stores/auth'
import Layout from '@/layout/Layout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/activate',
      name: 'Activate',
      component: () => import('@/views/activate/ActivateView.vue'),
      meta: { public: true, mode: 'activation' },
    },
    {
      path: '/reset-password',
      name: 'ResetPassword',
      component: () => import('@/views/activate/ActivateView.vue'),
      meta: { public: true, mode: 'reset_password' },
    },
    {
      path: '/',
      component: Layout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
          meta: { i18nKey: 'menu.dashboard' },
        },
        {
          path: 'approvals',
          name: 'ApprovalWorkbench',
          component: () => import('@/views/approval/ApprovalWorkbench.vue'),
          meta: { i18nKey: 'approval.title' },
        },
        {
          path: 'products/list',
          name: 'ProductList',
          component: () => import('@/views/products/ProductList.vue'),
          meta: { i18nKey: 'product.listTitle' },
        },
        {
          path: 'products/category',
          name: 'CategoryList',
          component: () => import('@/views/products/CategoryList.vue'),
          meta: { i18nKey: 'product.categoryTitle' },
        },
        {
          path: 'products/brand',
          name: 'BrandList',
          component: () => import('@/views/products/BrandList.vue'),
          meta: { i18nKey: 'product.brandTitle' },
        },
        {
          path: 'promotions/seckill',
          name: 'SeckillList',
          component: () => import('@/views/promotion/SeckillList.vue'),
          meta: { i18nKey: 'seckill.listTitle' },
        },
        {
          path: 'promotions/groupbuy',
          name: 'GroupBuyList',
          component: () => import('@/views/promotion/GroupBuyList.vue'),
          meta: { i18nKey: 'groupBuy.listTitle' },
        },
        {
          path: 'promotions/coupon',
          name: 'CouponList',
          component: () => import('@/views/promotion/CouponList.vue'),
          meta: { i18nKey: 'coupon.listTitle' },
        },
        {
          path: 'promotions/super-discount',
          name: 'SuperDiscountList',
          component: () => import('@/views/promotion/SuperDiscountList.vue'),
          meta: { i18nKey: 'superDiscount.listTitle' },
        },
        {
          path: 'subsidy/policies',
          name: 'SubsidyPolicyList',
          component: () => import('@/views/subsidy/PolicyList.vue'),
          meta: { i18nKey: 'subsidy.policyTitle' },
        },
        {
          path: 'subsidy/filings',
          name: 'SubsidyFilingMonitor',
          component: () => import('@/views/subsidy/FilingMonitorList.vue'),
          meta: { i18nKey: 'subsidy.monitorTitle' },
        },
        {
          path: 'subsidy/products',
          redirect: '/subsidy/filings',
        },
        {
          path: 'subsidy/stats',
          name: 'SubsidyStats',
          component: () => import('@/views/subsidy/StatsView.vue'),
          meta: { i18nKey: 'subsidy.statsTitle' },
        },
        {
          path: 'orders/list',
          name: 'OrderList',
          component: () => import('@/views/orders/OrderList.vue'),
          meta: { i18nKey: 'order.listTitle' },
        },
        {
          path: 'orders/refund',
          name: 'RefundList',
          component: () => import('@/views/orders/RefundList.vue'),
          meta: { i18nKey: 'order.refundTitle' },
        },
        {
          path: 'orders/logistics',
          name: 'LogisticsList',
          component: () => import('@/views/orders/LogisticsList.vue'),
          meta: { i18nKey: 'order.logisticsTitle' },
        },
        {
          path: 'customers/list',
          name: 'CustomerList',
          component: () => import('@/views/customers/CustomerList.vue'),
          meta: { i18nKey: 'customer.listTitle' },
        },
        {
          path: 'customers/membership-levels',
          name: 'MembershipLevelList',
          component: () => import('@/views/membership/LevelList.vue'),
          meta: { i18nKey: 'membership.listTitle' },
        },
        {
          path: 'customers/feedback',
          name: 'FeedbackList',
          component: () => import('@/views/customers/FeedbackList.vue'),
          meta: { i18nKey: 'feedback.listTitle' },
        },
        {
          path: 'customers/reviews',
          name: 'ReviewList',
          component: () => import('@/views/customers/ReviewList.vue'),
          meta: { i18nKey: 'review.manageTitle' },
        },
        {
          path: 'customers/chat',
          name: 'CustomerServiceWorkbench',
          component: () => import('@/views/customers/CustomerServiceWorkbench.vue'),
          meta: { i18nKey: 'chat.customerWorkbenchTitle' },
        },
        {
          path: 'customers/complaints',
          name: 'ComplaintList',
          component: () => import('@/views/customers/ComplaintList.vue'),
          meta: { i18nKey: 'complaint.listTitle' },
        },
        {
          path: 'customers/complaints/:id',
          name: 'ComplaintDetail',
          component: () => import('@/views/customers/ComplaintDetail.vue'),
          meta: { i18nKey: 'complaint.detailTitle' },
        },
        {
          path: 'reports/sales',
          name: 'ReportSales',
          component: () => import('@/views/reports/SalesReportView.vue'),
          meta: { i18nKey: 'report.salesTitle' },
        },
        {
          path: 'reports/product-rank',
          name: 'ReportProductRank',
          component: () => import('@/views/reports/ProductRankView.vue'),
          meta: { i18nKey: 'report.productRankTitle' },
        },
        {
          path: 'reports/customer',
          name: 'ReportCustomer',
          component: () => import('@/views/reports/CustomerAnalysisView.vue'),
          meta: { i18nKey: 'report.customerTitle' },
        },
        {
          path: 'reports/promotion',
          name: 'ReportPromotion',
          component: () => import('@/views/reports/PromotionAnalysisView.vue'),
          meta: { i18nKey: 'report.promotionTitle' },
        },
        {
          path: 'reports/finance',
          name: 'ReportFinance',
          component: () => import('@/views/reports/FinanceReportView.vue'),
          meta: { i18nKey: 'report.financeTitle' },
        },
        {
          path: 'reports/overview',
          redirect: '/reports/sales',
        },
        {
          path: 'org/chart',
          name: 'OrgChart',
          component: () => import('@/views/org/OrgChartView.vue'),
          meta: { i18nKey: 'org.title' },
        },
        {
          path: 'system/department',
          name: 'DepartmentManage',
          component: () => import('@/views/system/DepartmentView.vue'),
          meta: { i18nKey: 'system.department.title' },
        },
        {
          path: 'tenants/list',
          name: 'TenantList',
          component: () => import('@/views/system/TenantList.vue'),
          meta: { i18nKey: 'tenant.listTitle', permission: 'tenant:view' },
        },
        {
          path: 'tenants/appeals',
          name: 'AppealList',
          component: () => import('@/views/system/AppealList.vue'),
          meta: { i18nKey: 'appeal.listTitle', permission: 'tenant:appeal' },
        },
        {
          path: 'tenants/chat',
          name: 'TenantServiceWorkbench',
          component: () => import('@/views/tenants/TenantServiceWorkbench.vue'),
          meta: { i18nKey: 'tenant.chatTitle', permission: 'tenant:view' },
        },
        {
          path: 'tenants/pending-changes',
          name: 'TenantPendingChanges',
          component: () => import('@/views/tenants/PendingChangesList.vue'),
          meta: { i18nKey: 'tenant.pendingChangesTitle', permission: 'tenant:change:view' },
        },
        {
          path: 'tenants/shop-ratings',
          name: 'ShopRatingList',
          component: () => import('@/views/shop-rating/ShopRatingListView.vue'),
          meta: { i18nKey: 'shopRating.listTitle', permission: 'shop_rating:read' },
        },
        {
          path: 'tenants/:id',
          name: 'TenantDetail',
          component: () => import('@/views/system/TenantDetail.vue'),
          meta: { i18nKey: 'tenant.detailTitle', permission: 'tenant:view' },
        },
        {
          path: 'system/tenants',
          redirect: '/tenants/list',
        },
        {
          path: 'system/tenants/:id',
          redirect: (to) => ({ path: `/tenants/${to.params.id}` }),
        },
        {
          path: 'system/appeals',
          redirect: '/tenants/appeals',
        },
        {
          path: 'system/tenants/list',
          redirect: '/tenants/list',
        },
        {
          path: 'system/user',
          name: 'UserManage',
          component: () => import('@/views/system/UserList.vue'),
          meta: { i18nKey: 'system.user.title' },
        },
        {
          path: 'system/role',
          name: 'RoleManage',
          component: () => import('@/views/system/role/RoleView.vue'),
          meta: { i18nKey: 'system.role.title' },
        },
        {
          path: 'system/menu',
          name: 'MenuManage',
          component: () => import('@/views/system/menu/MenuView.vue'),
          meta: { i18nKey: 'system.menu.title' },
        },
        {
          path: 'system/audit',
          name: 'AuditLog',
          component: () => import('@/views/system/audit/AuditView.vue'),
          meta: { i18nKey: 'system.audit.title' },
        },
        {
          path: 'system/setting',
          name: 'SystemSetting',
          component: () => import('@/views/system/setting/SettingView.vue'),
          meta: { i18nKey: 'system.setting.title' },
        },
        {
          path: 'system/announcement',
          name: 'AnnouncementList',
          component: () => import('@/views/system/AnnouncementList.vue'),
          meta: { i18nKey: 'announcement.listTitle' },
        },
        {
          path: 'system/points',
          name: 'PointsManage',
          component: () => import('@/views/system/points/PointsManageView.vue'),
          meta: { i18nKey: 'points.manageTitle' },
        },
        {
          path: 'system/points-rules',
          name: 'PointsRules',
          component: () => import('@/views/system/points/PointsRulesView.vue'),
          meta: { i18nKey: 'points.rulesTitle' },
        },
        {
          path: 'system/seller-points',
          name: 'SellerPointsMonitor',
          component: () => import('@/views/system/points/SellerPointsMonitorView.vue'),
          meta: { i18nKey: 'points.sellerMonitorTitle' },
        },
        {
          path: 'system/points-mall/items',
          name: 'PointsMallItems',
          component: () => import('@/views/system/points/PointsMallItemsView.vue'),
          meta: { i18nKey: 'pointsMall.itemsTitle' },
        },
        {
          path: 'system/points-mall/orders',
          name: 'PointsMallOrders',
          component: () => import('@/views/system/points/PointsMallOrdersView.vue'),
          meta: { i18nKey: 'pointsMall.ordersTitle' },
        },
        {
          path: 'system/tags',
          name: 'TagList',
          component: () => import('@/views/system/tags/TagListView.vue'),
          meta: { i18nKey: 'tags.manageTitle' },
        },
        {
          path: 'system/tag-reviews',
          name: 'TagReview',
          component: () => import('@/views/system/tags/TagReviewView.vue'),
          meta: { i18nKey: 'tags.reviewTitle' },
        },
        {
          path: 'system/closures',
          name: 'ClosureList',
          component: () => import('@/views/system/closure/ClosureListView.vue'),
          meta: { i18nKey: 'closure.manageTitle' },
        },
        {
          path: 'announcements',
          name: 'AnnouncementCenter',
          component: () => import('@/views/announcements/AnnouncementCenter.vue'),
          meta: { i18nKey: 'announcement.centerTitle' },
        },
        {
          path: 'profile/change-password',
          name: 'ChangePassword',
          component: () => import('@/views/profile/ChangePassword.vue'),
          meta: { i18nKey: 'password.title' },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
})

router.beforeEach(async (to, from, next) => {
  if (to.meta.public) {
    if (to.path === '/login' && isLoggedIn()) {
      next('/dashboard')
      return
    }
    next()
    return
  }

  if (!isLoggedIn()) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  const authStore = useAuthStore()
  if (!authStore.user) {
    try {
      await authStore.fetchProfile()
    } catch {
      authStore.logout()
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
  }

  const { useRoleDisplayStore } = await import('@/stores/roleDisplay')
  const roleDisplayStore = useRoleDisplayStore()
  if (!roleDisplayStore.loaded) {
    await roleDisplayStore.fetchFromPublic()
  }

  if (
    authStore.user?.is_first_login
    && to.path !== '/profile/change-password'
    && !to.meta.public
  ) {
    next('/profile/change-password')
    return
  }

  next()
})

export default router
