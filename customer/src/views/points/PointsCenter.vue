<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { showDialog, showToast } from 'vant'
import {
  getMallPointsTransactions,
  getPointsProfile,
  getPublicPointsRules,
  signInPoints,
} from '@/api/points'
import { resolveErrorMessage } from '@/utils/feedback'

const { t } = useI18n()
const loading = ref(false)
const profile = ref(null)
const transactions = ref([])
const rules = ref([])
const rulesVisible = ref(false)

async function loadData() {
  loading.value = true
  try {
    const [profileRes, txnRes, rulesRes] = await Promise.all([
      getPointsProfile(),
      getMallPointsTransactions({ page_size: 20 }),
      getPublicPointsRules(),
    ])
    profile.value = profileRes.data
    transactions.value = txnRes.data.results || []
    rules.value = rulesRes.data || []
  } catch (error) {
    showToast(resolveErrorMessage(error, 'points.loadFailed'))
  } finally {
    loading.value = false
  }
}

async function handleSignIn() {
  if (profile.value?.signed_today) {
    showToast(t('points.alreadySigned'))
    return
  }
  try {
    const res = await signInPoints()
    showDialog({
      title: t('points.signInSuccessTitle'),
      message: t('points.signInSuccessMessage', {
        points: res.data.points_earned,
        days: res.data.consecutive_days,
      }),
    })
    await loadData()
  } catch (error) {
    showToast(resolveErrorMessage(error, 'points.signInFailed'))
  }
}

onMounted(loadData)
</script>

<template>
  <div class="points-page">
    <van-nav-bar :title="t('points.title')" left-arrow @click-left="$router.back()" />

    <van-skeleton v-if="loading" title :row="6" />

    <template v-else-if="profile">
      <div class="hero-card">
        <div class="hero-title">{{ t('points.available') }}</div>
        <div class="hero-value">{{ profile.balance.toLocaleString() }}</div>
        <div v-if="profile.balance_yuan_display" class="hero-worth">{{ profile.balance_yuan_display }}</div>
        <div class="hero-meta">
          <span>{{ t('points.totalEarned') }} {{ profile.total_earned }}</span>
          <span>{{ t('points.totalSpent') }} {{ profile.total_spent }}</span>
        </div>
        <div class="hero-actions">
          <van-button type="primary" round block :disabled="profile.signed_today" @click="handleSignIn">
            {{ profile.signed_today ? t('points.signedToday') : t('points.signIn') }}
          </van-button>
          <van-button round block plain hairline class="rules-btn" @click="$router.push({ name: 'PointsMall' })">
            {{ t('pointsMall.entry') }}
          </van-button>
          <van-button round block plain hairline class="rules-btn" @click="rulesVisible = true">
            {{ t('points.rules') }}
          </van-button>
        </div>
        <div v-if="profile.consecutive_days" class="streak">
          {{ t('points.consecutiveDays', { days: profile.consecutive_days }) }}
        </div>
        <div v-if="profile.balance_expire_at" class="expire-tip">
          {{ t('points.expiresAt', { date: profile.balance_expire_at.slice(0, 10) }) }}
        </div>
      </div>

      <div class="section-title">{{ t('points.transactions') }}</div>
      <van-cell-group inset>
        <van-cell
          v-for="item in transactions"
          :key="item.id"
          :title="item.description || item.trans_type_label"
          :label="item.created_at"
        >
          <template #value>
            <span :class="item.amount >= 0 ? 'plus' : 'minus'">
              {{ item.amount >= 0 ? '+' : '' }}{{ item.amount }}
            </span>
          </template>
        </van-cell>
        <van-empty v-if="!transactions.length" :description="t('points.noTransactions')" />
      </van-cell-group>
    </template>

    <van-popup v-model:show="rulesVisible" round position="bottom" :style="{ padding: '16px' }">
      <div class="rules-title">{{ t('points.rules') }}</div>
      <van-cell
        v-for="rule in rules"
        :key="rule.code"
        :title="rule.name"
        :label="rule.description"
        :value="String(rule.current_value ?? rule.points_value ?? 0)"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.points-page {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 24px;
}
.hero-card {
  margin: 12px 16px 0;
  padding: 20px 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #ffd666, #ffa940);
  color: #7c4a00;
}
.hero-title {
  font-size: 14px;
}
.hero-value {
  margin-top: 8px;
  font-size: 36px;
  font-weight: 700;
}
.hero-worth {
  margin-top: 4px;
  font-size: 14px;
  opacity: 0.9;
}
.hero-meta {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  font-size: 13px;
}
.hero-actions {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}
.rules-btn {
  background: rgba(255, 255, 255, 0.85);
}
.streak {
  margin-top: 10px;
  font-size: 13px;
}
.expire-tip {
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.85;
}
.section-title {
  margin: 20px 16px 8px;
  font-size: 16px;
  font-weight: 600;
}
.plus {
  color: #07c160;
  font-weight: 600;
}
.minus {
  color: #ee0a24;
  font-weight: 600;
}
.rules-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}
</style>
