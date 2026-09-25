<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getMyCoupons } from '@/api/promotion'
import { getPointsProfile } from '@/api/points'
import { getMembershipProfile, membershipCheckin } from '@/api/membership'
import { toastSuccess } from '@/utils/feedback'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useOrderSummaryStore } from '@/stores/orderSummary'
import { isLoggedIn } from '@/utils/auth'
import { requireLogin } from '@/stores/loginGate'
import { loadRecentProducts } from '@/utils/recentBrowse'
import { formatPrice, resolveImageUrl } from '@/utils/product'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const orderSummaryStore = useOrderSummaryStore()

const pointsBalance = ref(0)
const couponCount = ref(0)
const recentProducts = ref([])
const membershipProfile = ref(null)
const checkinLoading = ref(false)

const isGuest = computed(() => !isLoggedIn() || !authStore.isLoggedIn)

const displayName = computed(
  () => authStore.customer?.display_name
    || authStore.customer?.nickname
    || authStore.customer?.phone
    || t('profile.guestTitle'),
)

const memberLevelLabel = computed(() => {
  if (membershipProfile.value?.current_level?.name) {
    return membershipProfile.value.current_level.name
  }
  const level = authStore.customer?.level || 'normal'
  const map = {
    normal: t('profile.levelNormal'),
    silver: t('profile.levelSilver'),
    gold: t('profile.levelGold'),
    platinum: t('profile.levelPlatinum'),
    diamond: t('profile.levelDiamond'),
  }
  return map[level] || t('profile.levelNormal')
})

const avatarText = computed(() => displayName.value.charAt(0).toUpperCase())

const identityVerified = computed(() => Boolean(authStore.customer?.identity_verified))

const membershipProgressText = computed(() => {
  const profile = membershipProfile.value
  if (!profile) return ''
  if (profile.next_level) {
    return t('membership.growthProgress', {
      current: profile.growth_points.toLocaleString(),
      next: profile.next_level.min_points.toLocaleString(),
    })
  }
  return t('membership.maxLevel')
})

const membershipTipText = computed(() => {
  const profile = membershipProfile.value
  if (!profile?.next_level) return t('membership.maxLevelReached')
  return t('membership.pointsToNext', { points: profile.points_to_next.toLocaleString() })
})

const orderShortcuts = computed(() => [
  { key: 'pending', icon: 'balance-pay', label: t('profile.orderPending'), status: 'pending' },
  { key: 'paid', icon: 'logistics', label: t('profile.orderPaid'), status: 'paid' },
  { key: 'shipped', icon: 'send-gift-o', label: t('profile.orderShipped'), status: 'shipped' },
  { key: 'completed', icon: 'passed', label: t('profile.orderCompleted'), status: 'completed', noBadge: true },
  { key: 'pending_review', icon: 'comment-o', label: t('profile.orderPendingReview'), status: 'pending_review' },
  { key: 'aftersale', icon: 'after-sale', label: t('profile.orderAfterSale'), path: '/complaints' },
])

const featureShortcuts = computed(() => [
  { icon: 'medal-o', label: t('membership.benefitsTitle'), path: '/membership/benefits' },
  { icon: 'coupon-o', label: t('profile.myCoupons'), path: '/coupons' },
  { icon: 'gold-coin-o', label: t('profile.myPoints'), path: '/points' },
  { icon: 'gift-o', label: t('profile.pointsMall'), path: '/points-mall' },
  { icon: 'location-o', label: t('profile.address'), path: '/addresses' },
  { icon: 'service-o', label: t('profile.contactSupport'), path: '/chat' },
  { icon: 'comment-o', label: t('profile.reviews'), path: '/reviews' },
  { icon: 'star-o', label: t('profile.favorites'), path: '/profile' },
  { icon: 'chart-trending-o', label: t('profile.dataCenter'), path: '/points' },
  { icon: 'bell', label: t('notification.title'), path: '/notifications', badge: notificationStore.unreadCount },
])

async function openLogin() {
  try {
    await requireLogin({ redirect: '/profile' })
  } catch {
    // cancelled
  }
}

async function openProtected(path) {
  try {
    await requireLogin({ redirect: path })
    router.push(path)
  } catch {
    // cancelled
  }
}

function goOrders(status) {
  openProtected(status ? `/orders?status=${status}` : '/orders')
}

function goOrderShortcut(item) {
  if (item.path) {
    openProtected(item.path)
    return
  }
  goOrders(item.status)
}

async function loadMembershipProfile() {
  if (!isLoggedIn()) return
  try {
    const res = await getMembershipProfile()
    membershipProfile.value = res.data
  } catch {
    membershipProfile.value = null
  }
}

async function handleCheckin() {
  if (membershipProfile.value?.checked_in_today || checkinLoading.value) return
  checkinLoading.value = true
  try {
    const res = await membershipCheckin()
    membershipProfile.value = res.data
    toastSuccess(res.message || t('membership.checkinSuccess'))
  } catch {
    // handled by interceptor
  } finally {
    checkinLoading.value = false
  }
}

async function loadProfileStats() {
  if (!isLoggedIn()) return
  try {
    const [pointsRes, couponRes] = await Promise.all([
      getPointsProfile(),
      getMyCoupons({ status: 'unused', page_size: 1 }),
    ])
    pointsBalance.value = pointsRes.data?.balance ?? authStore.customer?.points ?? 0
    couponCount.value = couponRes.data?.count ?? (couponRes.data?.results?.length || 0)
  } catch {
    pointsBalance.value = authStore.customer?.points ?? 0
    couponCount.value = 0
  }
}

onMounted(async () => {
  recentProducts.value = loadRecentProducts().slice(0, 6)
  if (isLoggedIn()) {
    authStore.isLoggedIn = true
    if (!authStore.customer) {
      await authStore.hydrateSession()
    }
    notificationStore.refreshUnread()
    await Promise.all([loadProfileStats(), loadMembershipProfile(), orderSummaryStore.refresh()])
  } else {
    authStore.isLoggedIn = false
  }
})
</script>

<template>
  <div class="profile-page">
    <section class="user-card">
      <div class="user-card__top">
        <div class="user-main">
          <div class="avatar">{{ avatarText }}</div>
          <div class="user-info">
            <div class="user-name-row">
              <div class="user-name">{{ displayName }}</div>
              <span v-if="!isGuest" class="member-badge">👑 {{ t('profile.memberBadge') }}</span>
            </div>
            <div v-if="!isGuest" class="member-tag" @click="openProtected('/membership/benefits')">
              {{ memberLevelLabel }}
            </div>
            <div v-if="!isGuest && !identityVerified" class="identity-row">
              <span class="identity-status">{{ t('profile.identityUnverified') }}</span>
              <button
                type="button"
                class="identity-link"
                @click="openProtected('/profile/edit')"
              >
                {{ t('profile.identityVerifyHint') }}
              </button>
            </div>
            <div v-else-if="!isGuest && identityVerified" class="identity-verified">
              ✓ {{ t('profile.identityVerified') }}
            </div>
            <van-button v-else-if="isGuest" size="mini" round type="primary" class="login-btn" @click="openLogin">
              {{ t('auth.login') }} / {{ t('auth.registerNow') }}
            </van-button>
          </div>
        </div>
        <div class="user-actions">
          <button type="button" class="icon-btn" @click="openProtected('/notifications')">
            <van-badge :content="notificationStore.unreadCount || ''" :show-zero="false">
              <van-icon name="bell" size="20" />
            </van-badge>
          </button>
          <button type="button" class="icon-btn" @click="openProtected('/profile/settings')">
            <van-icon name="setting-o" size="20" />
          </button>
        </div>
      </div>

      <div v-if="!isGuest && membershipProfile" class="membership-panel" @click="openProtected('/membership/benefits')">
        <div class="membership-head">
          <span class="membership-level">👑 {{ membershipProfile.current_level?.name }}</span>
          <span class="membership-benefits">{{ membershipProfile.benefits_text }}</span>
        </div>
        <div class="membership-progress-text">{{ membershipProgressText }}</div>
        <van-progress
          :percentage="membershipProfile.progress_percent"
          stroke-width="6"
          color="#fff"
          track-color="rgba(255,255,255,0.25)"
          :show-pivot="false"
        />
        <div class="membership-foot">
          <span class="membership-tip">{{ membershipTipText }}</span>
          <van-button
            size="mini"
            round
            :type="membershipProfile.checked_in_today ? 'default' : 'primary'"
            :loading="checkinLoading"
            class="checkin-btn"
            @click.stop="handleCheckin"
          >
            {{
              membershipProfile.checked_in_today
                ? t('membership.checkedInToday')
                : t('membership.checkinAction')
            }}
          </van-button>
        </div>
        <div v-if="membershipProfile.checkin_streak > 0" class="streak-text">
          {{ t('membership.checkinStreak', { days: membershipProfile.checkin_streak }) }}
        </div>
      </div>

      <div v-if="!isGuest" class="asset-row">
        <button type="button" class="asset-item" @click="openProtected('/points')">
          <span class="asset-value">{{ pointsBalance.toLocaleString() }}</span>
          <span class="asset-label">{{ t('profile.pointsLabel') }}</span>
        </button>
        <button type="button" class="asset-item" @click="openProtected('/coupons')">
          <span class="asset-value">{{ couponCount }}</span>
          <span class="asset-label">{{ t('profile.couponLabel') }}</span>
        </button>
        <div class="asset-item">
          <span class="asset-value">¥0.00</span>
          <span class="asset-label">{{ t('profile.balanceLabel') }}</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <span class="panel-title">{{ t('profile.myOrders') }}</span>
        <button type="button" class="panel-link" @click="goOrders()">
          {{ t('profile.viewAll') }}
          <van-icon name="arrow" size="12" />
        </button>
      </div>
      <div class="order-grid">
        <button
          v-for="item in orderShortcuts"
          :key="item.key"
          type="button"
          class="shortcut-item"
          @click="goOrderShortcut(item)"
        >
          <van-badge
            :content="item.noBadge ? '' : orderSummaryStore.badgeForKey(item.key)"
            :show-zero="false"
          >
            <van-icon :name="item.icon" size="24" color="#e4393c" />
          </van-badge>
          <span>{{ item.label }}</span>
        </button>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <span class="panel-title">{{ t('profile.commonFeatures') }}</span>
      </div>
      <div class="feature-grid">
        <button
          v-for="item in featureShortcuts"
          :key="item.label"
          type="button"
          class="feature-item"
          @click="openProtected(item.path)"
        >
          <van-badge :content="item.badge || ''" :show-zero="false">
            <van-icon :name="item.icon" size="24" color="#666" />
          </van-badge>
          <span>{{ item.label }}</span>
        </button>
      </div>
    </section>

    <section v-if="recentProducts.length" class="panel">
      <div class="panel-head">
        <span class="panel-title">{{ t('profile.recentBrowse') }}</span>
      </div>
      <div class="recent-row">
        <article
          v-for="item in recentProducts"
          :key="item.id"
          class="recent-item"
          @click="router.push({ name: 'ProductDetail', params: { id: item.id } })"
        >
          <img :src="resolveImageUrl(item.image)" class="recent-img" alt="" />
          <div class="recent-name">{{ item.name }}</div>
          <div class="recent-price">{{ formatPrice(item.price) }}</div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100%;
  background: #f5f5f5;
  padding-bottom: 16px;
}

.user-card {
  margin: 12px;
  padding: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #e4393c 0%, #7c3aed 100%);
  color: #fff;
}

.user-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.user-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-info {
  min-width: 0;
}

.user-name {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.3;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.member-badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
  font-size: 11px;
  font-weight: 600;
}

.identity-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.identity-status {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 11px;
  font-weight: 600;
}

.identity-link {
  margin-top: 0;
  padding: 0;
  border: none;
  background: transparent;
  color: #fff;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  opacity: 0.95;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.identity-verified {
  margin-top: 6px;
  font-size: 12px;
  opacity: 0.95;
}

.member-tag {
  margin-top: 6px;
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
  font-size: 12px;
  cursor: pointer;
}

.membership-panel {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  cursor: pointer;
}

.membership-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.membership-level {
  font-size: 15px;
  font-weight: 700;
}

.membership-benefits {
  font-size: 12px;
  opacity: 0.95;
}

.membership-progress-text {
  font-size: 12px;
  margin-bottom: 8px;
  opacity: 0.95;
}

.membership-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 8px;
}

.membership-tip {
  font-size: 12px;
  opacity: 0.9;
}

.checkin-btn {
  flex-shrink: 0;
}

.streak-text {
  margin-top: 6px;
  font-size: 11px;
  opacity: 0.85;
}

.login-btn {
  margin-top: 8px;
}

.user-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.asset-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.asset-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: #fff;
  cursor: pointer;
  padding: 0;
}

.asset-value {
  font-size: 16px;
  font-weight: 700;
}

.asset-label {
  font-size: 12px;
  opacity: 0.9;
}

.panel {
  margin: 12px;
  padding: 14px 12px;
  background: #fff;
  border-radius: 12px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

.panel-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: #999;
  cursor: pointer;
}

.order-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px 8px;
}

.shortcut-item,
.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  padding: 4px 0;
  font-size: 12px;
  color: #666;
  cursor: pointer;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px 8px;
}

.recent-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.recent-row::-webkit-scrollbar {
  display: none;
}

.recent-item {
  flex: 0 0 88px;
  cursor: pointer;
}

.recent-img {
  width: 88px;
  height: 88px;
  border-radius: 8px;
  object-fit: cover;
  background: #f5f5f5;
}

.recent-name {
  margin-top: 6px;
  font-size: 12px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-price {
  margin-top: 2px;
  font-size: 12px;
  color: #e4393c;
  font-weight: 600;
}

.logout-wrap {
  margin: 12px;
}

@media (min-width: 992px) {
  .profile-page {
    max-width: 1280px;
    margin: 0 auto;
  }
}
</style>
