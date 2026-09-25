<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAlertStore } from '@/stores/alert'

const router = useRouter()
const { t } = useI18n()
const alertStore = useAlertStore()

const alert = computed(() => alertStore.latestAlert)

function handleClick() {
  const url = alert.value?.target_url
  const tenantId = alert.value?.tenant_id
  const conversationId = alert.value?.conversation_id
  alertStore.dismiss()
  if (url === '/customers/chat' && conversationId) {
    router.push({ path: url, query: { conversation_id: String(conversationId) } })
    return
  }
  if (url === '/tenants/chat' && conversationId) {
    router.push({ path: url, query: { conversation_id: String(conversationId) } })
    return
  }
  if (url) {
    router.push(url)
    return
  }
  if (conversationId) {
    router.push('/tenants/chat')
    return
  }
  if (tenantId) {
    router.push({ name: 'TenantDetail', params: { id: String(tenantId) }, query: { tab: 'changes' } })
  }
}

function handleClose() {
  alertStore.dismiss()
}
</script>

<template>
  <transition name="alert-slide">
    <div v-if="alertStore.visible && alert" class="global-system-alert" @click="handleClick">
      <div class="alert-inner">
        <strong>{{ alert.title }}</strong>
        <p>{{ alert.content }}</p>
        <span class="alert-action">{{ t('alert.clickToView') }}</span>
      </div>
      <button type="button" class="alert-close" @click.stop="handleClose">×</button>
    </div>
  </transition>
</template>

<style scoped>
.global-system-alert {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 3000;
  max-width: 420px;
  background: #fff1f0;
  border: 2px solid #f56c6c;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(245, 108, 108, 0.35);
  padding: 14px 40px 14px 16px;
  cursor: pointer;
  animation: shake 0.4s ease-in-out;
}

.alert-inner strong {
  display: block;
  color: #c45656;
  margin-bottom: 6px;
}

.alert-inner p {
  margin: 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

.alert-action {
  display: inline-block;
  margin-top: 8px;
  font-size: 12px;
  color: #409eff;
}

.alert-close {
  position: absolute;
  top: 8px;
  right: 10px;
  border: none;
  background: none;
  font-size: 20px;
  color: #909399;
  cursor: pointer;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.alert-slide-enter-active,
.alert-slide-leave-active {
  transition: all 0.25s ease;
}

.alert-slide-enter-from,
.alert-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
