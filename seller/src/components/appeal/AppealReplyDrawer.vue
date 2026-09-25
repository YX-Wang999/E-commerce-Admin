<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { useNotifyStore } from '@/stores/notify'

const { t } = useI18n()
const notifyStore = useNotifyStore()
const submitting = ref(false)

const visible = computed({
  get: () => notifyStore.drawerVisible,
  set: (value) => {
    if (!value) notifyStore.closeDrawer()
  },
})

const appeal = computed(() => notifyStore.appealDetail)

async function handleSend() {
  submitting.value = true
  try {
    const ok = await notifyStore.submitReply()
    if (ok) ElMessage.success(t('seller.replySent'))
  } catch (error) {
    ElMessage.error(error?.message || t('seller.sendFailed'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-drawer
    v-model="visible"
    :title="t('seller.appealReplyTitle')"
    size="480px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <div v-loading="notifyStore.loading" class="appeal-drawer">
      <template v-if="appeal">
        <div class="appeal-head">
          <h3>{{ appeal.title }}</h3>
          <el-tag size="small">{{ appeal.status }}</el-tag>
        </div>
        <p class="appeal-origin">{{ appeal.content }}</p>

        <div class="thread">
          <div
            v-for="msg in appeal.messages || []"
            :key="msg.id"
            class="thread-item"
            :class="msg.sender_type === 'platform' ? 'is-platform' : 'is-merchant'"
          >
            <div class="sender">{{ msg.sender_name }}</div>
            <div class="bubble">{{ msg.content }}</div>
            <div class="time">{{ new Date(msg.created_at).toLocaleString() }}</div>
          </div>
          <div v-if="!(appeal.messages || []).length && appeal.reply" class="thread-item is-platform">
            <div class="sender">{{ t('seller.platformSupport') }}</div>
            <div class="bubble">{{ appeal.reply }}</div>
          </div>
        </div>

        <div class="composer">
          <el-input
            v-model="notifyStore.replyText"
            type="textarea"
            :rows="4"
            :placeholder="t('seller.replyPlaceholder')"
          />
          <el-button type="primary" :loading="submitting" @click="handleSend">{{ t('seller.sendReply') }}</el-button>
        </div>
      </template>
    </div>
  </el-drawer>
</template>

<style scoped>
.appeal-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.appeal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.appeal-head h3 {
  margin: 0;
  font-size: 16px;
}

.appeal-origin {
  color: #606266;
  line-height: 1.6;
  margin: 0 0 16px;
}

.thread {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 16px;
}

.thread-item {
  margin-bottom: 16px;
}

.thread-item.is-platform .bubble {
  background: #f4f4f5;
}

.thread-item.is-merchant .bubble {
  background: #ecf5ff;
}

.sender {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.bubble {
  padding: 10px 12px;
  border-radius: 8px;
  line-height: 1.5;
  word-break: break-word;
}

.time {
  margin-top: 4px;
  font-size: 12px;
  color: #c0c4cc;
}

.composer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
