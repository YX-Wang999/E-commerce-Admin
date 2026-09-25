<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getMembershipLevels, getMembershipProfile } from '@/api/membership'
import { isLoggedIn } from '@/utils/auth'
import { requireLogin } from '@/stores/loginGate'

const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const profile = ref(null)
const levels = ref([])

const currentLevelValue = computed(() => profile.value?.current_level?.level || 1)

async function loadData() {
  loading.value = true
  try {
    if (!isLoggedIn()) {
      await requireLogin({ redirect: '/membership/benefits' })
    }
    const [profileRes, levelsRes] = await Promise.all([
      getMembershipProfile(),
      getMembershipLevels(),
    ])
    profile.value = profileRes.data
    levels.value = levelsRes.data || []
  } finally {
    loading.value = false
  }
}

function formatBenefits(level) {
  const parts = []
  if (level.discount_rate < 100) {
    parts.push(t('membership.discountBenefit', { rate: level.discount_rate }))
  }
  const multiplier = Number(level.points_multiplier)
  if (multiplier > 1) {
    parts.push(t('membership.pointsBenefit', { rate: multiplier }))
  }
  return parts.length ? parts.join(' + ') : t('membership.basicBenefit')
}

function isCurrent(level) {
  return level.level === currentLevelValue.value
}

function isUnlocked(level) {
  const growth = profile.value?.growth_points || 0
  return growth >= level.min_points
}

onMounted(loadData)
</script>

<template>
  <div class="benefits-page">
    <van-nav-bar
      :title="t('membership.benefitsTitle')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <div v-if="loading" class="loading-wrap">
      <van-loading size="24px">{{ t('common.loading') }}</van-loading>
    </div>

    <template v-else>
      <section v-if="profile" class="summary-card">
        <div class="summary-title">
          👑 {{ profile.current_level?.name }}
        </div>
        <div class="summary-sub">
          {{ t('membership.growthProgress', {
            current: profile.growth_points.toLocaleString(),
            next: profile.next_level ? profile.next_level.min_points.toLocaleString() : profile.growth_points.toLocaleString(),
          }) }}
        </div>
        <van-progress
          :percentage="profile.progress_percent"
          stroke-width="8"
          color="linear-gradient(90deg, #e4393c, #7c3aed)"
          track-color="#f0f0f0"
        />
        <div v-if="profile.next_level" class="summary-tip">
          {{ t('membership.pointsToNext', { points: profile.points_to_next.toLocaleString() }) }}
        </div>
        <div v-else class="summary-tip">{{ t('membership.maxLevel') }}</div>
        <div class="summary-benefits">{{ profile.benefits_text }}</div>
      </section>

      <section class="level-list">
        <h3>{{ t('membership.allLevels') }}</h3>
        <article
          v-for="level in levels"
          :key="level.id"
          class="level-card"
          :class="{ current: isCurrent(level), unlocked: isUnlocked(level) }"
        >
          <div class="level-head">
            <span class="level-name">{{ level.name }}</span>
            <van-tag v-if="isCurrent(level)" type="danger" round>{{ t('membership.currentTag') }}</van-tag>
          </div>
          <div class="level-meta">
            {{ t('membership.requiredPoints', { points: level.min_points.toLocaleString() }) }}
          </div>
          <div class="level-benefits">{{ formatBenefits(level) }}</div>
          <p v-if="level.description" class="level-desc">{{ level.description }}</p>
        </article>
      </section>
    </template>
  </div>
</template>

<style scoped>
.benefits-page {
  min-height: 100%;
  background: #f5f5f5;
  padding-bottom: 24px;
}

.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}

.summary-card {
  margin: 12px;
  padding: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #e4393c 0%, #7c3aed 100%);
  color: #fff;
}

.summary-title {
  font-size: 20px;
  font-weight: 700;
}

.summary-sub {
  margin: 8px 0 12px;
  font-size: 13px;
  opacity: 0.95;
}

.summary-tip {
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.9;
}

.summary-benefits {
  margin-top: 10px;
  font-size: 13px;
  font-weight: 600;
}

.level-list {
  margin: 12px;
}

.level-list h3 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #333;
}

.level-card {
  margin-bottom: 10px;
  padding: 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #eee;
}

.level-card.current {
  border-color: #e4393c;
  box-shadow: 0 0 0 1px rgba(228, 57, 60, 0.15);
}

.level-card.unlocked:not(.current) {
  opacity: 0.85;
}

.level-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.level-name {
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

.level-meta {
  margin-top: 6px;
  font-size: 12px;
  color: #999;
}

.level-benefits {
  margin-top: 8px;
  font-size: 14px;
  color: #e4393c;
  font-weight: 600;
}

.level-desc {
  margin: 8px 0 0;
  font-size: 12px;
  color: #666;
}
</style>
