<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { activateAccount } from '@/api/user'
import AuthPageShell from '@/components/auth/AuthPageShell.vue'
import { useAuthStore } from '@/stores/auth'

const REDIRECT_SECONDS = 3

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)
const linkInvalid = ref(false)
const completed = ref(false)
const countdown = ref(0)
const tipMessage = ref('')
const tipType = ref('info')

let countdownTimer = null

const mode = computed(() => route.meta.mode || 'activation')
const isResetMode = computed(() => mode.value === 'reset_password')
const i18nPrefix = computed(() => (isResetMode.value ? 'resetPassword' : 'activate'))

const uid = computed(() => route.query.uid || '')
const token = computed(() => route.query.token || '')

const form = reactive({
  password: '',
  confirm_password: '',
})

const rules = computed(() => {
  const validateConfirmPassword = (_rule, value, callback) => {
    if (value !== form.password) {
      callback(new Error(t('password.mismatch')))
      return
    }
    callback()
  }

  const passwordMinMessage = isResetMode.value
    ? t('resetPassword.passwordMin8')
    : t('activate.passwordMin8')

  return {
    password: [
      { required: true, message: t('password.newRequired'), trigger: 'blur' },
      { min: 8, message: passwordMinMessage, trigger: 'blur' },
    ],
    confirm_password: [
      { required: true, message: t('password.confirmRequired'), trigger: 'blur' },
      { validator: validateConfirmPassword, trigger: 'blur' },
    ],
  }
})

function tMode(key, params) {
  return t(`${i18nPrefix.value}.${key}`, params)
}

function showTip(message, type = 'info') {
  tipMessage.value = message
  tipType.value = type
}

function clearCountdownTimer() {
  if (countdownTimer !== null) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function redirectToLogin(username) {
  authStore.logout()
  const query = {
    username: username || undefined,
  }
  if (isResetMode.value) {
    query.reset = '1'
  } else {
    query.activated = '1'
  }
  router.push({ path: '/login', query })
}

function startRedirectCountdown(username) {
  completed.value = true
  countdown.value = REDIRECT_SECONDS
  showTip(tMode('successRedirect', { seconds: countdown.value }), 'success')

  clearCountdownTimer()
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value > 0) {
      showTip(tMode('successRedirect', { seconds: countdown.value }), 'success')
      return
    }
    clearCountdownTimer()
    redirectToLogin(username)
  }, 1000)
}

function resolveError(error) {
  const message = error?.message || error?.response?.data?.message || ''

  if (message.includes('已被使用')) {
    return t('activate.used')
  }
  if (message.includes('已失效')) {
    return tMode('used')
  }
  if (message.includes('过期')) {
    return tMode('expired')
  }
  if (message.includes('无效') || message.includes('不正确')) {
    return tMode('missingParams')
  }

  if (!error?.response && typeof error?.code !== 'number') {
    if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
      return tMode('networkError')
    }
    return tMode('networkError')
  }

  return message || tMode('networkError')
}

onMounted(() => {
  tipMessage.value = tMode('tipDefault')
  if (!uid.value || !token.value) {
    linkInvalid.value = true
    showTip(tMode('missingParams'), 'error')
    ElMessage.error(tMode('missingParams'))
  }
})

onBeforeUnmount(() => {
  clearCountdownTimer()
})

async function handleSubmit() {
  if (linkInvalid.value || completed.value) {
    if (linkInvalid.value) {
      ElMessage.error(tMode('missingParams'))
    }
    return
  }
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await activateAccount({
      uid: uid.value,
      token: token.value,
      password: form.password,
      mode: mode.value,
    })
    ElMessage.success(tMode('success'))
    startRedirectCountdown(res.data?.username || '')
  } catch (error) {
    const friendlyMessage = resolveError(error)
    showTip(friendlyMessage, 'error')
    ElMessage.error(friendlyMessage)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthPageShell :title="tMode('title')">
    <p class="activate-tip" :class="tipType">{{ tipMessage }}</p>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      size="large"
      :disabled="linkInvalid || completed"
      @keyup.enter="handleSubmit"
    >
      <el-form-item prop="password">
        <el-input
          v-model="form.password"
          type="password"
          show-password
          :placeholder="tMode('passwordPlaceholder')"
          :prefix-icon="Lock"
        />
      </el-form-item>
      <el-form-item prop="confirm_password">
        <el-input
          v-model="form.confirm_password"
          type="password"
          show-password
          :placeholder="tMode('confirmPlaceholder')"
          :prefix-icon="Lock"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          class="activate-btn"
          :loading="loading"
          :disabled="linkInvalid || completed"
          @click="handleSubmit"
        >
          {{ completed ? tMode('redirecting') : tMode('submitBtn') }}
        </el-button>
      </el-form-item>
    </el-form>
  </AuthPageShell>
</template>

<style scoped>
.activate-tip {
  margin: -8px 0 24px;
  text-align: center;
  font-size: 14px;
  color: #606266;
}

.activate-tip.success {
  color: #67c23a;
}

.activate-tip.error {
  color: #f56c6c;
}

.activate-btn {
  width: 100%;
  min-height: 44px;
}
</style>
