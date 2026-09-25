<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AuthPhoneField from '@/components/auth/AuthPhoneField.vue'
import { resolveErrorMessage, toastError, toastSuccess } from '@/utils/feedback'
import { isValidE164Phone } from '@/utils/phone'
import { useAuthStore } from '@/stores/auth'
import { useLoginGateStore } from '@/stores/loginGate'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const loginGate = useLoginGateStore()

const loading = ref(false)
const form = reactive({
  phone: '',
  password: '',
})

const phoneRules = computed(() => [
  { required: true, message: t('auth.phoneRequired') },
  { validator: () => isValidE164Phone(form.phone), message: t('auth.phoneInvalid') },
])

const visible = computed({
  get: () => loginGate.visible,
  set: (value) => {
    if (!value) {
      loginGate.cancel()
    }
  },
})

function closeSheet() {
  loginGate.cancel()
}

async function handleLogin() {
  if (!isValidE164Phone(form.phone)) {
    toastError(t('auth.phoneInvalid'))
    return
  }
  if (!form.password.trim()) {
    toastError(t('auth.passwordRequired'))
    return
  }

  loading.value = true
  try {
    const result = await authStore.login({
      login_mode: 'phone_password',
      phone: form.phone.trim(),
      password: form.password,
    })
    toastSuccess(t('auth.loginSuccess'))
    if (result.mergedGuestCount > 0) {
      toastSuccess(t('cart.guestMerged', { count: result.mergedGuestCount }))
    }
    loginGate.succeed()
    const redirect = loginGate.redirect || '/'
    if (redirect && redirect !== router.currentRoute.value.fullPath) {
      router.push(redirect)
    }
  } catch (error) {
    toastError(resolveErrorMessage(error, 'auth.loginFailed'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <van-popup
    v-model:show="visible"
    position="bottom"
    round
    closeable
    safe-area-inset-bottom
    :style="{ maxHeight: '88vh' }"
    @close="closeSheet"
  >
    <div class="login-sheet">
      <div class="sheet-header">
        <h2>{{ t('auth.loginSheetTitle') }}</h2>
        <p>{{ t('auth.loginSheetSubtitle') }}</p>
      </div>

      <van-form class="auth-form" @submit="handleLogin">
        <AuthPhoneField
          v-model="form.phone"
          :placeholder="t('auth.phonePlaceholder')"
          :rules="phoneRules"
        />
        <van-field
          v-model="form.password"
          type="password"
          name="password"
          :label="t('auth.password')"
          :placeholder="t('auth.passwordPlaceholder')"
          clearable
        />
        <van-button type="primary" native-type="submit" block round :loading="loading" class="submit-btn">
          {{ t('auth.login') }}
        </van-button>
      </van-form>

      <div class="sheet-footer">
        <router-link to="/register" class="link" @click="closeSheet">{{ t('auth.registerNow') }}</router-link>
        <router-link to="/login" class="link" @click="closeSheet">{{ t('auth.fullLoginPage') }}</router-link>
      </div>
    </div>
  </van-popup>
</template>

<style scoped>
.login-sheet {
  padding: 8px 20px 24px;
}

.sheet-header {
  padding: 8px 8px 16px;
  text-align: center;
}

.sheet-header h2 {
  margin: 0;
  font-size: 20px;
  color: #323233;
}

.sheet-header p {
  margin: 8px 0 0;
  font-size: 13px;
  color: #969799;
}

.submit-btn {
  margin-top: 16px;
  height: 44px;
}

.sheet-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
}

.link {
  color: #1989fa;
  font-size: 14px;
  text-decoration: none;
}
</style>
