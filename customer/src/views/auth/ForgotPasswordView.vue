<script setup>
import { computed, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { resetPassword, sendSms } from '@/api/auth'
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
let smsTimer = null

const form = reactive({
  phone: '',
  sms_code: '',
  password: '',
  confirmPassword: '',
})

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
    const res = await sendSms({ phone: form.phone.trim(), scene: 'reset_password' })
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

async function handleSubmit() {
  loading.value = true
  try {
    const res = await resetPassword({
      phone: form.phone.trim(),
      sms_code: form.sms_code.trim(),
      password: form.password,
    })
    toastSuccess(res.message || t('auth.resetPasswordSuccess'))
    router.push('/login')
  } catch (error) {
    toastError(resolveErrorMessage(error, 'auth.resetPasswordFailed'))
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
    <div class="forgot-header">
      <h1>{{ t('auth.forgotTitle') }}</h1>
      <p>{{ t('auth.forgotSubtitle') }}</p>
    </div>

    <van-form :key="locale" class="auth-form" @submit="handleSubmit">
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
          :label="t('auth.newPassword')"
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
      </van-cell-group>

      <van-button type="primary" native-type="submit" block round :loading="loading" class="submit-btn">
        {{ t('auth.resetPassword') }}
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
.forgot-header {
  margin-bottom: 24px;
  text-align: center;
}
.forgot-header h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  color: #333;
}
.forgot-header p {
  margin: 8px 0 0;
  color: #999;
  font-size: 14px;
  line-height: 1.5;
}
.submit-btn {
  height: 44px;
  font-size: 16px;
  margin-top: 8px;
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
