<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { forgotPassword, getCaptcha, getCaptchaTrust } from '@/api/auth'
import AuthPageShell from '@/components/auth/AuthPageShell.vue'
import SliderCaptcha from '@/components/auth/SliderCaptcha.vue'
import {
  DEMO_ACCOUNTS,
  DEMO_PASSWORD,
  REMEMBER_USERNAME_KEY,
} from '@/config/app'
import { useAuthStore } from '@/stores/auth'
import { getDeviceId } from '@/utils/device'
import { unlockAlertSound } from '@/utils/alertSound'

const FORGOT_PASSWORD_COOLDOWN = 60

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const authStore = useAuthStore()

const formRef = ref(null)
const forgotFormRef = ref(null)
const submitting = ref(false)
const loginError = ref('')
const remainingAttempts = ref(null)
const rememberUsername = ref(false)
const captchaLoading = ref(false)
const captchaVerified = ref(false)
const captchaActivated = ref(false)
const captchaDialogVisible = ref(false)
const trustLevel = ref('medium')
const trustLoading = ref(false)
const forgotDialogVisible = ref(false)
const forgotSubmitting = ref(false)
const forgotCooldown = ref(0)
const pendingLoginRetry = ref(false)

let forgotCooldownTimer = null

const captcha = reactive({
  id: '',
  background: '',
  offset: 0,
  width: 278,
  height: 155,
})

const form = reactive({
  username: '',
  password: '',
})

const forgotForm = reactive({
  email: '',
})

const showLowTrustGate = computed(() => trustLevel.value === 'low')

const forgotRules = computed(() => ({
  email: [
    { required: true, message: t('login.forgotPasswordEmailRequired'), trigger: 'blur' },
    { type: 'email', message: t('login.forgotPasswordEmailInvalid'), trigger: 'blur' },
  ],
}))

const forgotSubmitLabel = computed(() => {
  if (forgotCooldown.value > 0) {
    return t('login.forgotPasswordCooldown', { seconds: forgotCooldown.value })
  }
  return t('login.forgotPasswordSubmit')
})

const rules = computed(() => ({
  username: [{ required: true, message: t('login.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('login.passwordRequired'), trigger: 'blur' }],
}))

const LOGIN_ERROR_MAP = {
  40001: 'login.usernameRequired',
  40002: 'login.invalidCredentials',
  40003: 'login.accountDisabled',
  40004: 'login.accountLocked',
  40005: 'login.captchaInvalid',
  40006: 'login.usernameNotFound',
  40007: 'login.passwordWrong',
}

function resolveLoginError(error) {
  const code = error?.code
  const key = LOGIN_ERROR_MAP[code]
  if (key) {
    return t(key)
  }
  if (error?.message && !error.message.startsWith('Request failed with status code')) {
    return error.message
  }
  return t('login.failed')
}

function applyCaptchaData(data = {}) {
  captcha.id = data.captcha_id || ''
  captcha.background = data.background || ''
  captcha.offset = data.offset ?? 0
  captcha.width = data.width ?? 278
  captcha.height = data.height ?? 155
}

function resetCaptchaState() {
  captchaVerified.value = false
  captcha.id = ''
  captcha.background = ''
  captcha.offset = 0
}

function loadRememberedUsername() {
  const saved = localStorage.getItem(REMEMBER_USERNAME_KEY)
  if (saved) {
    form.username = saved
    rememberUsername.value = true
  }
}

function persistRememberedUsername() {
  if (rememberUsername.value && form.username) {
    localStorage.setItem(REMEMBER_USERNAME_KEY, form.username.trim())
    return
  }
  localStorage.removeItem(REMEMBER_USERNAME_KEY)
}

async function fetchTrustLevel() {
  trustLoading.value = true
  try {
    const res = await getCaptchaTrust({
      username: form.username.trim() || undefined,
    })
    trustLevel.value = res.data.trust_level || 'medium'
    if (trustLevel.value !== 'low') {
      captchaActivated.value = false
      resetCaptchaState()
    }
  } catch {
    trustLevel.value = 'medium'
  } finally {
    trustLoading.value = false
  }
}

async function refreshCaptcha() {
  captchaLoading.value = true
  captchaVerified.value = false
  try {
    const res = await getCaptcha()
    applyCaptchaData(res.data)
  } catch {
    loginError.value = t('login.failed')
  } finally {
    captchaLoading.value = false
  }
}

async function activateCaptcha() {
  captchaActivated.value = true
  await refreshCaptcha()
}

function handleCaptchaSuccess() {
  captchaVerified.value = true
  if (pendingLoginRetry.value) {
    pendingLoginRetry.value = false
    captchaDialogVisible.value = false
    handleLogin()
  }
}

function handleCaptchaFail(error) {
  captchaVerified.value = false
  if (error?.code === 404) {
    loginError.value = t('login.captchaApiNotFound')
    return
  }
  if (error?.message && !error.message.startsWith('Request failed with status code')) {
    loginError.value = error.message
  }
}

function handleCaptchaRequired(error) {
  const data = error?.data || {}
  if (!data.require_captcha) {
    return false
  }

  if (data.trust_level) {
    trustLevel.value = data.trust_level
  }

  if (data.captcha_mode === 'post_login') {
    applyCaptchaData(data)
    captchaDialogVisible.value = true
    loginError.value = t('login.captchaPostLoginHint')
    return true
  }

  trustLevel.value = 'low'
  captchaActivated.value = false
  resetCaptchaState()
  loginError.value = t('login.captchaPreActionHint')
  return true
}

async function handleLogin() {
  void unlockAlertSound()
  loginError.value = ''
  remainingAttempts.value = null

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  if (trustLevel.value === 'low' && !captchaVerified.value) {
    loginError.value = t('login.captchaPreActionHint')
    return
  }

  submitting.value = true
  try {
    const payload = {
      username: form.username.trim(),
      password: form.password,
      device_id: getDeviceId(),
    }
    if (captchaVerified.value && captcha.id) {
      payload.captcha_id = captcha.id
    }

    const res = await authStore.login(payload)
    persistRememberedUsername()

    if (res.code === 1001) {
      ElMessage.warning(res.message || t('login.firstLogin'))
      router.push('/profile/change-password')
      return
    }

    ElMessage.success(t('login.success'))
    router.push('/dashboard')
  } catch (error) {
    if (handleCaptchaRequired(error)) {
      if (error?.data?.captcha_mode === 'post_login') {
        pendingLoginRetry.value = true
      }
      return
    }

    loginError.value = resolveLoginError(error)
    if (typeof error?.data?.remaining_attempts === 'number') {
      remainingAttempts.value = error.data.remaining_attempts
    }
    captchaVerified.value = false
    if (trustLevel.value === 'low' && captchaActivated.value) {
      await refreshCaptcha()
    }
    await fetchTrustLevel()
  } finally {
    submitting.value = false
  }
}

function clearForgotCooldownTimer() {
  if (forgotCooldownTimer !== null) {
    clearInterval(forgotCooldownTimer)
    forgotCooldownTimer = null
  }
}

function startForgotCooldown() {
  forgotCooldown.value = FORGOT_PASSWORD_COOLDOWN
  clearForgotCooldownTimer()
  forgotCooldownTimer = setInterval(() => {
    forgotCooldown.value -= 1
    if (forgotCooldown.value <= 0) {
      clearForgotCooldownTimer()
    }
  }, 1000)
}

function handleForgotPassword() {
  forgotDialogVisible.value = true
}

async function handleSendResetEmail() {
  if (forgotCooldown.value > 0) {
    return
  }
  try {
    await forgotFormRef.value.validate()
  } catch {
    return
  }

  forgotSubmitting.value = true
  try {
    await forgotPassword({ email: forgotForm.email.trim() })
    ElMessage.success(t('login.forgotPasswordSuccess'))
    startForgotCooldown()
    forgotDialogVisible.value = false
    forgotForm.email = ''
    forgotFormRef.value?.clearValidate()
  } catch (error) {
    ElMessage.error(error?.message || t('login.failed'))
  } finally {
    forgotSubmitting.value = false
  }
}

function fillDemoAccount(username) {
  form.username = username
  form.password = DEMO_PASSWORD
  loginError.value = ''
  fetchTrustLevel()
}

onMounted(async () => {
  loadRememberedUsername()
  const activatedUsername = route.query.username
  if (typeof activatedUsername === 'string' && activatedUsername) {
    form.username = activatedUsername
  }
  if (route.query.activated === '1') {
    ElMessage.success(t('activate.success'))
  }
  if (route.query.reset === '1') {
    ElMessage.success(t('resetPassword.success'))
  }
  await fetchTrustLevel()
})

onBeforeUnmount(() => {
  clearForgotCooldownTimer()
})
</script>

<template>
  <AuthPageShell :title="t('login.title')">
    <el-alert
      v-if="loginError"
      :title="loginError"
      type="error"
      show-icon
      :closable="false"
      class="login-alert"
    />
    <p v-if="remainingAttempts !== null && remainingAttempts > 0" class="login-hint">
      {{ t('login.remainingAttempts', { count: remainingAttempts }) }}
    </p>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      size="large"
      @submit.prevent="handleLogin"
    >
      <el-form-item prop="username">
        <el-input
          v-model="form.username"
          :placeholder="t('login.username')"
          :prefix-icon="User"
          autocomplete="username"
          @blur="fetchTrustLevel"
        />
      </el-form-item>

      <el-form-item prop="password">
        <el-input
          v-model="form.password"
          type="password"
          :placeholder="t('login.password')"
          show-password
          :prefix-icon="Lock"
          autocomplete="current-password"
        />
      </el-form-item>

      <el-form-item v-if="showLowTrustGate">
        <div class="captcha-gate">
          <button
            v-if="!captchaActivated"
            type="button"
            class="captcha-gate__trigger"
            :disabled="trustLoading"
            @click="activateCaptcha"
          >
            <span class="captcha-gate__title">{{ t('login.captchaClickToStart') }}</span>
            <span class="captcha-gate__hint">{{ t('login.captchaPreActionHint') }}</span>
          </button>
          <SliderCaptcha
            v-else
            :captcha-id="captcha.id"
            :background="captcha.background"
            :offset="captcha.offset"
            :width="captcha.width"
            :height="captcha.height"
            :loading="captchaLoading"
            @success="handleCaptchaSuccess"
            @fail="handleCaptchaFail"
            @refresh="refreshCaptcha"
          />
        </div>
      </el-form-item>

      <div class="login-options">
        <el-checkbox v-model="rememberUsername">{{ t('login.rememberUsername') }}</el-checkbox>
        <el-button link type="primary" @click="handleForgotPassword">
          {{ t('login.forgotPassword') }}
        </el-button>
      </div>

      <el-form-item>
        <el-button
          type="primary"
          native-type="submit"
          class="login-btn"
          :loading="submitting || authStore.loading"
        >
          {{ t('login.submit') }}
        </el-button>
      </el-form-item>
    </el-form>

    <div class="demo-panel">
      <div class="demo-panel__title">{{ t('login.demoAccounts') }}</div>
      <p class="demo-panel__hint">{{ t('login.demoPasswordHint') }}</p>
      <div class="demo-tags">
        <el-tag
          v-for="item in DEMO_ACCOUNTS"
          :key="item.username"
          class="demo-tag"
          effect="plain"
          @click="fillDemoAccount(item.username)"
        >
          {{ t(item.labelKey) }}
        </el-tag>
      </div>
    </div>
  </AuthPageShell>

  <el-dialog
    v-model="captchaDialogVisible"
    :title="t('login.captchaDialogTitle')"
    width="340px"
    align-center
    destroy-on-close
    :close-on-click-modal="false"
    @closed="pendingLoginRetry = false"
  >
    <p class="captcha-dialog__hint">{{ t('login.captchaPostLoginHint') }}</p>
    <SliderCaptcha
      :captcha-id="captcha.id"
      :background="captcha.background"
      :offset="captcha.offset"
      :width="captcha.width"
      :height="captcha.height"
      :loading="captchaLoading"
      @success="handleCaptchaSuccess"
      @fail="handleCaptchaFail"
      @refresh="refreshCaptcha"
    />
  </el-dialog>

  <el-dialog
    v-model="forgotDialogVisible"
    :title="t('login.forgotPasswordTitle')"
    width="420px"
    destroy-on-close
  >
    <el-form
      ref="forgotFormRef"
      :model="forgotForm"
      :rules="forgotRules"
      label-position="top"
      @submit.prevent="handleSendResetEmail"
    >
      <el-form-item :label="t('login.forgotPasswordEmail')" prop="email">
        <el-input
          v-model="forgotForm.email"
          type="email"
          :placeholder="t('login.forgotPasswordEmailPlaceholder')"
          autocomplete="email"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="forgotDialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button
        type="primary"
        :loading="forgotSubmitting"
        :disabled="forgotCooldown > 0"
        @click="handleSendResetEmail"
      >
        {{ forgotSubmitLabel }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.login-alert {
  margin-bottom: 16px;
}

.login-hint {
  margin: -8px 0 12px;
  font-size: 13px;
  color: #e6a23c;
}

.captcha-gate {
  width: 100%;
}

.captcha-gate__trigger {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  min-height: 205px;
  padding: 20px;
  border: 1px dashed #c0c4cc;
  border-radius: 8px;
  background: #f5f7fa;
  color: #606266;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.captcha-gate__trigger:hover:not(:disabled) {
  border-color: #409eff;
  background: #ecf5ff;
}

.captcha-gate__trigger:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.captcha-gate__title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.captcha-gate__hint {
  font-size: 12px;
  color: #909399;
}

.captcha-dialog__hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: #606266;
}

.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.login-btn {
  width: 100%;
  min-height: 44px;
}

.demo-panel {
  margin-top: 8px;
  padding-top: 20px;
  border-top: 1px dashed #ebeef5;
}

.demo-panel__title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 4px;
}

.demo-panel__hint {
  margin: 0 0 10px;
  font-size: 12px;
  color: #909399;
}

.demo-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.demo-tag {
  cursor: pointer;
}

@media (max-width: 575px) {
  .login-options {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
