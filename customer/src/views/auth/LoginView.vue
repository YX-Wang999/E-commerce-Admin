<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { login, sendSms } from '@/api/auth'
import AuthShell from '@/components/auth/AuthShell.vue'
import AuthPhoneField from '@/components/auth/AuthPhoneField.vue'
import LocaleSwitcher from '@/components/common/LocaleSwitcher.vue'
import { resolveErrorMessage, toastError, toastSuccess } from '@/utils/feedback'
import { isValidE164Phone } from '@/utils/phone'
import { useAuthStore } from '@/stores/auth'

const REMEMBER_ACCOUNT_KEY = 'remembered_account'
const REMEMBER_MODE_KEY = 'remembered_login_mode'
const SMS_COUNTDOWN_SECONDS = 60

const LOGIN_MODES = {
  PHONE_PASSWORD: 'phone_password',
  PHONE_SMS: 'phone_sms',
  ACCOUNT_PASSWORD: 'account_password',
}

const router = useRouter()
const route = useRoute()
const { t, locale } = useI18n()
const authStore = useAuthStore()
const loading = ref(false)
const smsLoading = ref(false)
const smsCountdown = ref(0)
const remember = ref(true)

const savedMode = localStorage.getItem(REMEMBER_MODE_KEY)
const loginMode = ref(
  Object.values(LOGIN_MODES).includes(savedMode) ? savedMode : LOGIN_MODES.PHONE_PASSWORD,
)

const form = reactive({
  phone: '',
  account: localStorage.getItem(REMEMBER_ACCOUNT_KEY) || '',
  password: '',
  sms_code: '',
})

let smsTimer = null

const phoneRules = computed(() => [
  { required: true, message: t('auth.phoneRequired') },
  { validator: () => isValidE164Phone(form.phone), message: t('auth.phoneInvalid') },
])

const accountRules = computed(() => [
  { required: true, message: t('auth.accountRequired') },
])

const formRules = computed(() => {
  const rules = {}
  if (loginMode.value !== LOGIN_MODES.ACCOUNT_PASSWORD) {
    rules.phone = phoneRules.value
  } else {
    rules.account = accountRules.value
  }
  if (loginMode.value === LOGIN_MODES.PHONE_SMS) {
    rules.sms_code = [{ required: true, message: t('auth.smsCodeRequired') }]
  } else {
    rules.password = [{ required: true, message: t('auth.passwordRequired') }]
  }
  return rules
})

const loginSubtitle = computed(() => {
  if (loginMode.value === LOGIN_MODES.PHONE_PASSWORD) {
    return t('auth.loginSubtitlePhonePassword')
  }
  if (loginMode.value === LOGIN_MODES.PHONE_SMS) {
    return t('auth.loginSubtitlePhoneSms')
  }
  return t('auth.loginSubtitleAccount')
})

const modeOptions = computed(() => [
  { value: LOGIN_MODES.PHONE_PASSWORD, label: t('auth.modePhonePassword') },
  { value: LOGIN_MODES.PHONE_SMS, label: t('auth.modePhoneSms') },
  { value: LOGIN_MODES.ACCOUNT_PASSWORD, label: t('auth.modeAccountPassword') },
])

function switchLoginMode(mode) {
  if (loginMode.value === mode) {
    return
  }
  loginMode.value = mode
  form.password = ''
  form.sms_code = ''
}

function startSmsCountdown() {
  smsCountdown.value = SMS_COUNTDOWN_SECONDS
  smsTimer = setInterval(() => {
    smsCountdown.value -= 1
    if (smsCountdown.value <= 0) {
      clearInterval(smsTimer)
      smsTimer = null
    }
  }, 1000)
}

async function handleSendSms() {
  if (!isValidE164Phone(form.phone)) {
    toastError(t('auth.phoneInvalid'))
    return
  }
  smsLoading.value = true
  try {
    const res = await sendSms({ phone: form.phone.trim(), scene: 'login' })
    if (res.data?.dev_code) {
      toastSuccess(t('auth.smsSentDev', { code: res.data.dev_code }))
    } else {
      toastSuccess(res.message || t('auth.smsSent'))
    }
    startSmsCountdown()
  } catch (error) {
    toastError(resolveErrorMessage(error, 'auth.smsSendFailed'))
  } finally {
    smsLoading.value = false
  }
}

function persistRemembered() {
  if (!remember.value) {
    localStorage.removeItem(REMEMBER_ACCOUNT_KEY)
    localStorage.removeItem(REMEMBER_MODE_KEY)
    return
  }
  localStorage.setItem(REMEMBER_MODE_KEY, loginMode.value)
  if (loginMode.value === LOGIN_MODES.ACCOUNT_PASSWORD) {
    localStorage.setItem(REMEMBER_ACCOUNT_KEY, form.account.trim())
  } else {
    localStorage.setItem(REMEMBER_ACCOUNT_KEY, form.phone.trim())
  }
}

onMounted(() => {
  if (loginMode.value !== LOGIN_MODES.ACCOUNT_PASSWORD && localStorage.getItem(REMEMBER_ACCOUNT_KEY)) {
    form.phone = localStorage.getItem(REMEMBER_ACCOUNT_KEY)
  }
  if (form.account || form.phone) {
    remember.value = true
  }
})

onUnmounted(() => {
  if (smsTimer) {
    clearInterval(smsTimer)
  }
})

async function handleLogin() {
  loading.value = true
  try {
    const payload = { login_mode: loginMode.value }
    if (loginMode.value === LOGIN_MODES.ACCOUNT_PASSWORD) {
      payload.account = form.account.trim()
      payload.password = form.password
    } else if (loginMode.value === LOGIN_MODES.PHONE_PASSWORD) {
      payload.phone = form.phone.trim()
      payload.password = form.password
    } else {
      payload.phone = form.phone.trim()
      payload.sms_code = form.sms_code.trim()
    }

    const result = await authStore.login(payload)
    persistRemembered()
    toastSuccess(t('auth.loginSuccess'))
    if (result.mergedGuestCount > 0) {
      toastSuccess(t('cart.guestMerged', { count: result.mergedGuestCount }))
    }
    const redirect = route.query.redirect || '/'
    router.push(typeof redirect === 'string' ? redirect : '/')
  } catch (error) {
    toastError(resolveErrorMessage(error, 'auth.loginFailed'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell>
    <div class="locale-row">
      <LocaleSwitcher />
    </div>
    <div class="login-header">
      <h1>{{ t('auth.welcomeBack') }}</h1>
      <p>{{ loginSubtitle }}</p>
    </div>

    <div class="mode-tabs">
      <button
        v-for="item in modeOptions"
        :key="item.value"
        type="button"
        class="mode-tab"
        :class="{ active: loginMode === item.value }"
        @click="switchLoginMode(item.value)"
      >
        {{ item.label }}
      </button>
    </div>

    <van-form :key="`${locale}-${loginMode}`" class="auth-form" @submit="handleLogin">
      <van-cell-group :border="false">
        <AuthPhoneField
          v-if="loginMode !== LOGIN_MODES.ACCOUNT_PASSWORD"
          v-model="form.phone"
          :placeholder="t('auth.phonePlaceholder')"
          :rules="formRules.phone"
        />
        <van-field
          v-else
          v-model="form.account"
          name="account"
          :label="t('auth.account')"
          :placeholder="t('auth.accountPlaceholder')"
          :rules="formRules.account"
          clearable
        />

        <van-field
          v-if="loginMode === LOGIN_MODES.PHONE_SMS"
          v-model="form.sms_code"
          maxlength="6"
          :label="t('auth.smsCode')"
          :placeholder="t('auth.smsCodePlaceholder')"
          :rules="formRules.sms_code"
        >
          <template #button>
            <van-button
              size="small"
              type="primary"
              plain
              native-type="button"
              :loading="smsLoading"
              :disabled="smsCountdown > 0"
              @click.prevent="handleSendSms"
            >
              {{ smsCountdown > 0 ? t('auth.smsResendIn', { seconds: smsCountdown }) : t('auth.sendSms') }}
            </van-button>
          </template>
        </van-field>

        <van-field
          v-if="loginMode !== LOGIN_MODES.PHONE_SMS"
          v-model="form.password"
          type="password"
          name="password"
          :label="t('auth.password')"
          :placeholder="t('auth.passwordPlaceholder')"
          :rules="formRules.password"
        />
      </van-cell-group>

      <div class="login-options">
        <van-checkbox v-model="remember">{{ t('auth.rememberAccount') }}</van-checkbox>
        <router-link to="/forgot-password" class="link">{{ t('auth.forgotPassword') }}</router-link>
      </div>

      <van-button type="primary" native-type="submit" block round :loading="loading" class="submit-btn">
        {{ t('auth.login') }}
      </van-button>
    </van-form>

    <div class="footer-link">
      {{ t('auth.noAccount') }}
      <router-link to="/register" class="link">{{ t('auth.registerNow') }}</router-link>
    </div>
  </AuthShell>
</template>

<style scoped>
.locale-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
.login-header {
  margin-bottom: 20px;
  text-align: center;
}
.login-header h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  color: #333;
}
.login-header p {
  margin: 8px 0 0;
  color: #999;
  font-size: 14px;
}
.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.mode-tab {
  flex: 1;
  min-width: 0;
  padding: 8px 6px;
  border: 1px solid #ebedf0;
  border-radius: 8px;
  background: #f7f8fa;
  color: #646566;
  font-size: 12px;
  line-height: 1.3;
  cursor: pointer;
  transition: all 0.2s;
}
.mode-tab.active {
  border-color: #1989fa;
  background: #ecf5ff;
  color: #1989fa;
  font-weight: 600;
}
.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 12px 0 24px;
}
.link {
  color: #1989fa;
  font-size: 14px;
  text-decoration: none;
}
.submit-btn {
  height: 44px;
  font-size: 16px;
}
.footer-link {
  margin-top: 20px;
  text-align: center;
  color: #999;
  font-size: 14px;
}
</style>
