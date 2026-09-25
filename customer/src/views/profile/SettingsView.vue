<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import SubPageNav from '@/components/layout/SubPageNav.vue'
import { confirmDialog } from '@/utils/confirmDialog'
import { toastSuccess } from '@/utils/feedback'
import { useAuthStore } from '@/stores/auth'
import { LOCALE_OPTIONS, setLocale, getLocale } from '@/i18n'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

const languageVisible = ref(false)

const currentLocaleLabel = computed(() => {
  const current = getLocale()
  const item = LOCALE_OPTIONS.find((option) => option.value === current)
  return item ? t(item.labelKey) : current
})

const languageActions = computed(() =>
  LOCALE_OPTIONS.map((item) => ({
    name: t(item.labelKey),
    value: item.value,
  })),
)

function selectLanguage(action) {
  if (action?.value) {
    setLocale(action.value)
    toastSuccess(t('settings.languageUpdated'))
  }
  languageVisible.value = false
}

function goPersonalInfo() {
  router.push({ name: 'ProfileEdit' })
}

async function handleLogout() {
  try {
    await confirmDialog({ title: t('common.tip'), message: t('profile.logoutConfirm') })
    authStore.logout()
    const { useCartStore } = await import('@/stores/cart')
    useCartStore().loadGuestCart()
    toastSuccess(t('profile.logoutSuccess'))
    router.replace({ name: 'Home' })
  } catch {
    // cancelled
  }
}

async function handleSwitchAccount() {
  try {
    await confirmDialog({ title: t('common.tip'), message: t('settings.switchAccountConfirm') })
    authStore.logout()
    const { useCartStore } = await import('@/stores/cart')
    useCartStore().loadGuestCart()
    router.push({ name: 'Login', query: { redirect: '/profile' } })
  } catch {
    // cancelled
  }
}
</script>

<template>
  <div class="settings-page">
    <SubPageNav :title="t('settings.title')" />
    <van-cell-group inset :title="t('settings.accountSection')">
      <van-cell
        :title="t('settings.personalInfo')"
        is-link
        @click="goPersonalInfo"
      />
      <van-cell
        :title="t('settings.language')"
        :value="currentLocaleLabel"
        is-link
        @click="languageVisible = true"
      />
    </van-cell-group>

    <van-cell-group inset :title="t('settings.sessionSection')">
      <van-cell
        :title="t('settings.switchAccount')"
        is-link
        @click="handleSwitchAccount"
      />
      <van-cell
        :title="t('profile.logout')"
        is-link
        class="logout-cell"
        @click="handleLogout"
      />
    </van-cell-group>

    <van-action-sheet
      v-model:show="languageVisible"
      :title="t('settings.language')"
      :actions="languageActions"
      :cancel-text="t('common.cancel')"
      close-on-click-action
      @select="selectLanguage"
    />
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100%;
  background: #f5f5f5;
  padding: 12px 0 24px;
}

.logout-cell :deep(.van-cell__title) {
  color: #ee0a24;
}
</style>
