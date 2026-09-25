<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getSellerPointsRule, updateSellerPointsRule } from '@/api/sellerPoints'

const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)

const form = reactive({
  points_name: '',
  earn_rate: 1,
  max_earn_per_order: 1000,
  redeem_rate: 100,
  max_redeem_rate: 30,
  expire_days: 365,
  is_active: true,
})

async function fetchRule() {
  loading.value = true
  try {
    const res = await getSellerPointsRule()
    Object.assign(form, res.data || {})
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  saving.value = true
  try {
    const res = await updateSellerPointsRule({ ...form })
    Object.assign(form, res.data || {})
    ElMessage.success(t('sellerPoints.saveSuccess'))
  } catch {
    ElMessage.error(t('seller.saveFailed'))
  } finally {
    saving.value = false
  }
}

onMounted(fetchRule)
</script>

<template>
  <div v-loading="loading" class="page-card">
    <h2>{{ t('sellerPoints.ruleTitle') }}</h2>
    <p class="page-tip">{{ t('sellerPoints.ruleTip') }}</p>

    <el-form label-width="160px" class="rule-form">
      <el-form-item :label="t('sellerPoints.pointsName')">
        <el-input v-model="form.points_name" maxlength="50" />
      </el-form-item>
      <el-form-item :label="t('sellerPoints.earnRate')">
        <el-input-number v-model="form.earn_rate" :min="0" :max="10" :step="0.1" :precision="2" />
        <span class="field-hint">{{ t('sellerPoints.earnRateHint') }}</span>
      </el-form-item>
      <el-form-item :label="t('sellerPoints.maxEarnPerOrder')">
        <el-input-number v-model="form.max_earn_per_order" :min="0" :step="100" />
      </el-form-item>
      <el-form-item :label="t('sellerPoints.redeemRate')">
        <el-input-number v-model="form.redeem_rate" :min="100" :max="1000" :step="10" />
        <span class="field-hint">{{ t('sellerPoints.redeemRateHint') }}</span>
      </el-form-item>
      <el-form-item :label="t('sellerPoints.maxRedeemRate')">
        <el-input-number v-model="form.max_redeem_rate" :min="0" :max="50" :step="5" />
        <span class="field-hint">%</span>
      </el-form-item>
      <el-form-item :label="t('sellerPoints.expireDays')">
        <el-input-number v-model="form.expire_days" :min="30" :step="30" />
      </el-form-item>
      <el-form-item :label="t('sellerPoints.isActive')">
        <el-switch v-model="form.is_active" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSubmit">
          {{ t('sellerPoints.saveRule') }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.page-tip {
  margin: 0 0 16px;
  color: #909399;
  font-size: 13px;
}

.rule-form {
  max-width: 640px;
}

.field-hint {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}
</style>
