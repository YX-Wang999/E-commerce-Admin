<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import SubPageNav from '@/components/layout/SubPageNav.vue'
import { showToast } from 'vant'
import { updateProfile } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { toastSuccess } from '@/utils/feedback'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

const submitting = ref(false)
const form = reactive({
  nickname: '',
  email: '',
  real_name: '',
})

const phone = computed(() => authStore.customer?.phone || '')
const identityVerified = computed(() => Boolean(authStore.customer?.identity_verified))

async function loadForm() {
  await authStore.fetchProfile()
  const customer = authStore.customer || {}
  form.nickname = customer.nickname || customer.display_name || ''
  form.email = customer.email || ''
  form.real_name = customer.real_name || ''
}

async function handleSubmit() {
  if (!form.nickname.trim()) {
    showToast(t('settings.nicknameRequired'))
    return
  }
  submitting.value = true
  try {
    const res = await updateProfile({
      nickname: form.nickname.trim(),
      email: form.email.trim(),
      real_name: form.real_name.trim(),
    })
    authStore.customer = res.data
    toastSuccess(res.message || t('settings.saveSuccess'))
    router.back()
  } finally {
    submitting.value = false
  }
}

onMounted(loadForm)
</script>

<template>
  <div class="profile-edit-page">
    <SubPageNav :title="t('settings.personalInfo')" />
    <van-form @submit="handleSubmit">
      <van-cell-group inset>
        <van-field
          v-model="form.nickname"
          :label="t('settings.nickname')"
          :placeholder="t('settings.nicknamePlaceholder')"
          maxlength="32"
          required
        />
        <van-field
          v-model="phone"
          :label="t('settings.phone')"
          readonly
        />
        <van-field
          v-model="form.email"
          :label="t('settings.email')"
          :placeholder="t('settings.emailPlaceholder')"
          type="email"
        />
        <van-field
          v-model="form.real_name"
          :label="t('settings.realName')"
          :placeholder="t('settings.realNamePlaceholder')"
          maxlength="32"
        />
      </van-cell-group>

      <div class="identity-tip">
        <van-tag v-if="identityVerified" type="success">{{ t('profile.identityVerified') }}</van-tag>
        <van-tag v-else type="warning">{{ t('profile.identityUnverified') }}</van-tag>
        <span class="identity-tip__text">{{ t('settings.realNameTip') }}</span>
      </div>

      <div class="submit-wrap">
        <van-button round block type="primary" native-type="submit" :loading="submitting">
          {{ t('settings.saveAction') }}
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<style scoped>
.profile-edit-page {
  min-height: 100%;
  background: #f5f5f5;
  padding: 12px 0 24px;
}

.identity-tip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 16px 0;
}

.identity-tip__text {
  font-size: 12px;
  color: #969799;
  line-height: 1.5;
}

.submit-wrap {
  margin: 24px 16px 0;
}
</style>
