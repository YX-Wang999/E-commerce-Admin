<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { updateTenantProfile } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()
const saving = ref(false)

const form = reactive({
  payment_methods: 'online',
  settlement_account: '',
  settlement_note: '',
})

function syncForm() {
  const config = authStore.tenant?.config || {}
  form.payment_methods = config.payment_methods || 'online'
  form.settlement_account = config.settlement_account || ''
  form.settlement_note = config.settlement_note || ''
}

async function handleSubmit() {
  saving.value = true
  try {
    const config = {
      ...(authStore.tenant?.config || {}),
      payment_methods: form.payment_methods,
      settlement_account: form.settlement_account.trim(),
      settlement_note: form.settlement_note.trim(),
    }
    const res = await updateTenantProfile({ config })
    if (res.data?.tenant) {
      authStore.tenant = res.data.tenant
    }
    ElMessage.success(t('seller.saveSettings'))
  } catch {
    ElMessage.error(t('seller.saveFailed'))
  } finally {
    saving.value = false
  }
}

onMounted(syncForm)
</script>

<template>
  <div class="page-card">
    <h2>{{ t('seller.menuPaymentSettings') }}</h2>
    <p class="page-tip">{{ t('seller.paymentSettingsTip') }}</p>

    <el-form label-width="120px" class="settings-form">
      <el-form-item :label="t('seller.paymentMethods')">
        <el-radio-group v-model="form.payment_methods">
          <el-radio value="online">{{ t('seller.paymentOnline') }}</el-radio>
          <el-radio value="cod">{{ t('seller.paymentCod') }}</el-radio>
          <el-radio value="both">{{ t('seller.paymentBoth') }}</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item :label="t('seller.settlementAccount')">
        <el-input
          v-model="form.settlement_account"
          maxlength="120"
          :placeholder="t('seller.settlementAccountPlaceholder')"
        />
      </el-form-item>
      <el-form-item :label="t('seller.settlementNote')">
        <el-input
          v-model="form.settlement_note"
          type="textarea"
          :rows="3"
          maxlength="300"
          show-word-limit
          :placeholder="t('seller.settlementNotePlaceholder')"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSubmit">
          {{ t('seller.saveSettings') }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}
.page-card h2 {
  margin: 0 0 8px;
  font-size: 18px;
}
.page-tip {
  margin: 0 0 20px;
  color: #909399;
  font-size: 13px;
}
.settings-form {
  max-width: 640px;
}
</style>
