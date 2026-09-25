<script setup>
import { computed, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { register, sendSms } from '@/api/auth'
import AuthShell from '@/components/auth/AuthShell.vue'
import AuthPhoneField from '@/components/auth/AuthPhoneField.vue'
import LocaleSwitcher from '@/components/common/LocaleSwitcher.vue'
import { resolveErrorMessage, toastError, toastSuccess } from '@/utils/feedback'
import { isValidE164Phone } from '@/utils/phone'

const SMS_COUNTDOWN_SECONDS = 10

const router = useRouter()
const { t, locale } = useI18n()
const loading = ref(false)
const smsLoading = ref(false)
const smsCountdown = ref(0)
const errorMessage = ref('')
let smsTimer = null

const form = reactive({
  phone: '',
  sms_code: '',
  password: '',
  confirmPassword: '',
  nickname: '',
  email: '',
})

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const formRules = computed(() => ({
  phone: [
    { required: true, message: t('auth.phoneRequired') },
    { validator: () => isValidE164Phone(form.phone), message: t('auth.phoneInvalid') },
  ],
  sms_code: [{ required: true, message: t('auth.smsCodeRequired') }],
  password: [
    { required: true, message: t('auth.passwordRequired') },
    { validator: (val) => val.length >= 8, message: t('auth.passwordMin') },
  ],
  confirmPassword: [
    { required: true, message: t('auth.confirmPasswordRequired') },
    { validator: (val) => val === form.password, message: t('auth.passwordMismatch') },
  ],
  email: [
    {
      validator: (val) => !val || emailPattern.test(val),
      message: t('auth.emailInvalid'),
    },
  ],
}))

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
    const res = await sendSms({ phone: form.phone.trim(), scene: 'register' })
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

async function handleRegister() {
  errorMessage.value = ''
  loading.value = true
  try {
    const res = await register({
      phone: form.phone.trim(),
      sms_code: form.sms_code.trim(),
      password: form.password,
      nickname: form.nickname.trim() || undefined,
      email: form.email.trim() || undefined,
    })
    toastSuccess(res.message || t('auth.registerSuccess'))
    router.push('/login')
  } catch (error) {
    const message = resolveErrorMessage(error, 'auth.registerFailed')
    errorMessage.value = message
    toastError(message)
  } finally {
    loading.value = false
  }
}

onUnmounted(() => {
  if (smsTimer) {
    clearInterval(smsTimer)
  }
})
</script>

<template>
  <AuthShell>
    <div class="locale-row">
      <LocaleSwitcher />
    </div>
    <div class="register-header">
      <h1>{{ t('auth.createAccount') }}</h1>
      <p>{{ t('auth.registerSubtitle') }}</p>
    </div>

    <div v-if="errorMessage" class="error-banner" role="alert">{{ errorMessage }}</div>

    <van-form :key="locale" class="auth-form" @submit="handleRegister">
      <van-cell-group :border="false">
        <AuthPhoneField
          v-model="form.phone"
          :placeholder="t('auth.phonePlaceholder')"
          :rules="formRules.phone"
        />
        <van-field
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
          v-model="form.password"
          type="password"
          :label="t('auth.password')"
          :placeholder="t('auth.registerPasswordPlaceholder')"
          :rules="formRules.password"
        />
        <van-field
          v-model="form.confirmPassword"
          type="password"
          :label="t('auth.confirmPassword')"
          :placeholder="t('auth.confirmPasswordPlaceholder')"
          :rules="formRules.confirmPassword"
        />
        <van-field
          v-model="form.nickname"
          :label="t('auth.nickname')"
          :placeholder="t('auth.nicknamePlaceholder')"
        />
        <van-field
          v-model="form.email"
          :label="t('auth.emailOptional')"
          :placeholder="t('auth.emailOptionalPlaceholder')"
          :rules="formRules.email"
        />
      </van-cell-group>

      <van-button type="primary" native-type="submit" block round :loading="loading" class="submit-btn">
        {{ t('auth.register') }}
      </van-button>
    </van-form>

    <div class="footer-link">
      <router-link to="/login" class="link">{{ t('auth.backToLogin') }}</router-link>
    </div>
  </AuthShell>
</template>

<style scoped>
.locale-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
.register-header {
  margin-bottom: 24px;
  text-align: center;
}
.register-header h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  color: #333;
}
.register-header p {
  margin: 8px 0 0;
  color: #999;
}
.error-banner {
  margin-bottom: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  color: #cf1322;
  font-size: 14px;
  line-height: 1.5;
}
.submit-btn {
  height: 44px;
  font-size: 16px;
  margin-top: 16px;
}
.footer-link {
  margin-top: 20px;
  text-align: center;
}
.link {
  color: #1989fa;
  text-decoration: none;
  font-size: 14px;
}
</style>
