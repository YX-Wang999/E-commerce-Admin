<script setup>
import { computed, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { WarningFilled, CircleCloseFilled, Clock, Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { submitAppeal, openAppealChat } from '@/api/tenant'
import GuestPlatformChat from '@/components/appeal/GuestPlatformChat.vue'
import LocaleSwitcher from '@/components/LocaleSwitcher.vue'
import { unlockAlertSound } from '@/utils/alertSound'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const authStore = useAuthStore()
const formRef = ref()
const appealFormRef = ref()
const loading = ref(false)
const submitting = ref(false)

const showErrorDialog = ref(false)
const showAppealDialog = ref(false)
const showChatDialog = ref(false)
const chatConversationId = ref(null)
const chatMerchantUserId = ref(null)
const chatOpening = ref(false)
const errorType = ref('')
const errorTitle = ref('')
const errorMessage = ref('')
const errorDetail = ref(null)

const form = reactive({
  account: '',
  password: '',
})

const appealForm = reactive({
  title: '',
  content: '',
  attachments: [],
})

const rules = {
  account: [{ required: true, message: () => t('seller.accountRequired'), trigger: 'blur' }],
  password: [{ required: true, message: () => t('seller.passwordRequired'), trigger: 'blur' }],
}

const appealRules = computed(() => ({
  title: [{ required: true, message: t('seller.appealTitleRequired'), trigger: 'blur' }],
  content: [{ required: true, message: t('seller.appealContentRequired'), trigger: 'blur' }],
}))

const canAppeal = computed(() => ['suspended', 'closed', 'pending'].includes(errorType.value))

const errorDialogTitle = computed(() => {
  const map = {
    pending: t('seller.statusPendingTitle'),
    suspended: t('seller.statusSuspendedTitle'),
    closed: t('seller.statusClosedTitle'),
  }
  return map[errorType.value] || t('seller.loginFailed')
})

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function handleLoginError(error) {
  if (error?.code === 403 && error?.data?.status) {
    showErrorDialog.value = true
    errorType.value = error.data.status
    errorTitle.value = errorDialogTitle.value
    errorMessage.value = error.message || t('seller.loginFailed')
    errorDetail.value = error.data
    return
  }
  ElMessage.error(error?.message || t('seller.loginFailed'))
}

function showContactInfo() {
  const contact = errorDetail.value?.contact || {}
  ElMessageBox.alert(
    `${t('seller.contactPhoneLabel')}：${contact.phone || '400-888-8888'}\n${t('seller.contactEmailLabel')}：${contact.email || 'service@platform.com'}`,
    t('seller.contactSupport'),
    { confirmButtonText: t('seller.appealConfirmOk') },
  )
}

function openAppealDialog() {
  appealForm.title = ''
  appealForm.content = ''
  appealForm.attachments = []
  showAppealDialog.value = true
}

async function openPlatformChat() {
  if (!form.account.trim() || !form.password) {
    ElMessage.warning(t('seller.appealChatNeedCredentials'))
    return
  }
  chatOpening.value = true
  try {
    const res = await openAppealChat({
      account: form.account.trim(),
      password: form.password,
    })
    chatConversationId.value = res.data.conversation_id
    chatMerchantUserId.value = res.data.user_id
    showChatDialog.value = true
    showErrorDialog.value = false
    ElMessage.success(t('seller.appealChatConnected'))
  } catch (error) {
    ElMessage.error(error?.message || t('seller.appealChatOpenFailed'))
  } finally {
    chatOpening.value = false
  }
}

async function handleLogin() {
  void unlockAlertSound()
  await formRef.value?.validate()
  loading.value = true
  try {
    await authStore.login(form)
    ElMessage.success(t('seller.loginSuccess'))
    const redirect = route.query.redirect || '/'
    router.push(String(redirect))
  } catch (error) {
    handleLoginError(error)
  } finally {
    loading.value = false
  }
}

async function submitAppealForm() {
  await appealFormRef.value?.validate()
  submitting.value = true
  try {
    await submitAppeal({
      account: form.account,
      password: form.password,
      title: appealForm.title,
      content: appealForm.content,
      attachments: appealForm.attachments,
    })
    ElMessage.success(t('seller.appealSubmitSuccess'))
    showAppealDialog.value = false
    showErrorDialog.value = false
  } catch (error) {
    ElMessage.error(error?.message || t('seller.appealSubmitFailed'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="seller-login">
    <div class="locale-bar">
      <LocaleSwitcher compact />
    </div>
    <div class="login-card">
      <div class="login-header">
        <h1>🏪 {{ t('seller.loginTitle') }}</h1>
        <p>{{ t('seller.loginSubtitle') }}</p>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
        <el-form-item prop="account">
          <el-input
            v-model="form.account"
            :placeholder="t('seller.account')"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="t('seller.password')"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" size="large" :loading="loading" style="width: 100%">
            {{ loading ? t('seller.loggingIn') : t('seller.login') }}
          </el-button>
        </el-form-item>
        <div class="login-footer">
          <router-link to="/apply">{{ t('seller.applyLink') }}</router-link>
        </div>
      </el-form>
    </div>

    <el-dialog
      v-model="showErrorDialog"
      :title="errorDialogTitle"
      width="520px"
      :close-on-click-modal="false"
    >
      <div class="error-content">
        <el-icon class="error-icon" :size="48">
          <Clock v-if="errorType === 'pending'" style="color: #e6a23c" />
          <WarningFilled v-else-if="errorType === 'suspended'" style="color: #e6a23c" />
          <CircleCloseFilled v-else style="color: #f56c6c" />
        </el-icon>
        <h3>{{ errorMessage }}</h3>
        <p v-if="errorDetail?.hint" class="error-hint">{{ errorDetail.hint }}</p>

        <div v-if="errorType !== 'pending' && errorDetail?.reason" class="error-detail">
          <p><strong>{{ t('seller.reasonLabel') }}：</strong>{{ errorDetail.reason }}</p>
          <p v-if="errorDetail.detail?.description">
            <strong>{{ t('seller.detailLabel') }}：</strong>{{ errorDetail.detail.description }}
          </p>
          <p v-if="errorDetail.detail?.violations?.length">
            <strong>{{ t('seller.violationLabel') }}：</strong>
            <span v-for="(item, index) in errorDetail.detail.violations" :key="index" class="violation-tag">
              {{ item }}
            </span>
          </p>
          <p v-if="errorDetail.suspended_at">
            <strong>{{ t('seller.suspendedAtLabel') }}：</strong>{{ formatDate(errorDetail.suspended_at) }}
          </p>
        </div>

        <div class="error-actions">
          <el-button v-if="canAppeal" type="primary" @click="openAppealDialog">
            {{ t('seller.onlineAppeal') }}
          </el-button>
          <el-button v-if="canAppeal" :loading="chatOpening" @click="openPlatformChat">
            {{ t('seller.contactPlatformChat') }}
          </el-button>
          <el-button @click="showContactInfo">{{ t('seller.contactSupport') }}</el-button>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showAppealDialog" :title="t('seller.appealDialogTitle')" width="600px">
      <el-form :model="appealForm" :rules="appealRules" ref="appealFormRef" label-width="90px">
        <el-form-item :label="t('seller.appealTitleLabel')" prop="title">
          <el-input v-model="appealForm.title" :placeholder="t('seller.appealTitlePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('seller.appealContentLabel')" prop="content">
          <el-input
            v-model="appealForm.content"
            type="textarea"
            :rows="6"
            :placeholder="t('seller.appealContentPlaceholder')"
          />
        </el-form-item>
        <p class="form-tip">{{ t('seller.appealAttachmentTip') }}</p>
      </el-form>
      <template #footer>
        <el-button @click="showAppealDialog = false">{{ t('seller.appealCancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitAppealForm">
          {{ t('seller.appealSubmit') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showChatDialog"
      :title="t('seller.appealChatTitle')"
      width="640px"
      :close-on-click-modal="false"
    >
      <GuestPlatformChat
        v-if="showChatDialog && chatConversationId"
        :account="form.account"
        :password="form.password"
        :conversation-id="chatConversationId"
        :merchant-user-id="chatMerchantUserId"
      />
    </el-dialog>
  </div>
</template>

<style scoped>
.seller-login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  position: relative;
}

.locale-bar {
  position: absolute;
  top: 20px;
  right: 24px;
}

.locale-bar :deep(.locale-btn-compact) {
  color: rgba(255, 255, 255, 0.9);
}

.login-card {
  width: 420px;
  padding: 40px 32px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 24px;
  color: #1a1a2e;
  margin: 0;
}

.login-header p {
  color: #999;
  margin-top: 8px;
}

.login-footer {
  text-align: center;
  font-size: 14px;
}

.login-footer a {
  color: #409eff;
}

.error-content {
  text-align: center;
  padding: 8px 0 0;
}

.error-icon {
  margin-bottom: 16px;
}

.error-content h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: #303133;
}

.error-hint {
  color: #909399;
  margin: 0 0 12px;
}

.error-detail {
  text-align: left;
  background: #f5f6fa;
  padding: 16px;
  border-radius: 8px;
  margin: 16px 0;
  line-height: 1.8;
}

.error-detail p {
  margin: 0 0 8px;
}

.error-detail p:last-child {
  margin-bottom: 0;
}

.violation-tag {
  display: inline-block;
  margin-right: 8px;
  padding: 2px 8px;
  background: #fef0f0;
  color: #f56c6c;
  border-radius: 4px;
  font-size: 12px;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}

.form-tip {
  margin: 0;
  font-size: 12px;
  color: #909399;
}
</style>
