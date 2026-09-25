<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getExpressCompanies } from '@/api/orders'
import { updateTenantProfile } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()
const saving = ref(false)
const expressCompanies = ref([])

const form = reactive({
  default_express_code: '',
  shipping_note: '',
})

const expressOptions = computed(() =>
  expressCompanies.value.map((item) => ({
    label: item.name,
    value: item.code,
  })),
)

function syncForm() {
  const config = authStore.tenant?.config || {}
  form.default_express_code = config.default_express_code || ''
  form.shipping_note = config.shipping_note || ''
}

async function loadExpressCompanies() {
  try {
    const res = await getExpressCompanies()
    expressCompanies.value = res.data || []
  } catch {
    expressCompanies.value = []
  }
}

async function handleSubmit() {
  saving.value = true
  try {
    const config = {
      ...(authStore.tenant?.config || {}),
      default_express_code: form.default_express_code,
      shipping_note: form.shipping_note.trim(),
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

onMounted(async () => {
  syncForm()
  await loadExpressCompanies()
})
</script>

<template>
  <div class="page-card">
    <h2>{{ t('seller.menuLogisticsSettings') }}</h2>
    <p class="page-tip">{{ t('seller.logisticsSettingsTip') }}</p>

    <el-form label-width="120px" class="settings-form">
      <el-form-item :label="t('seller.defaultExpress')">
        <el-select v-model="form.default_express_code" clearable filterable style="width: 320px">
          <el-option
            v-for="item in expressOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('seller.shippingNote')">
        <el-input
          v-model="form.shipping_note"
          type="textarea"
          :rows="4"
          maxlength="500"
          show-word-limit
          :placeholder="t('seller.shippingNotePlaceholder')"
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
