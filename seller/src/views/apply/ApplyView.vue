<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { applyTenant, checkApplyField } from '@/api/auth'
import { validateTenantName } from '@/utils/tenantName'

const router = useRouter()
const { t } = useI18n()
const formRef = ref()
const loading = ref(false)
const fieldErrors = reactive({ name: '', contact_name: '', contact_phone: '' })
const fieldWarnings = reactive({ name: '' })

const form = reactive({
  name: '',
  contact_name: '',
  contact_phone: '',
  contact_email: '',
  address: '',
  password: '',
  confirmPassword: '',
})

const rules = computed(() => ({
  name: [
    { required: true, message: t('seller.shopNameRequired'), trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        const formatError = validateTenantName(value)
        if (formatError) {
          callback(new Error(formatError))
          return
        }
        if (fieldErrors.name) {
          callback(new Error(fieldErrors.name))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  contact_name: [
    { required: true, message: t('seller.contactRequired'), trigger: 'blur' },
    {
      validator: (_rule, _value, callback) => {
        if (fieldErrors.contact_name) {
          callback(new Error(fieldErrors.contact_name))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  contact_phone: [
    { required: true, message: t('seller.phoneRequired'), trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: t('seller.phoneInvalid'), trigger: 'blur' },
    {
      validator: (_rule, _value, callback) => {
        if (fieldErrors.contact_phone) {
          callback(new Error(fieldErrors.contact_phone))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  contact_email: [
    { required: true, message: t('seller.emailRequired'), trigger: 'blur' },
    { type: 'email', message: t('seller.emailInvalid'), trigger: 'blur' },
  ],
  password: [
    { required: true, message: t('seller.passwordRequired'), trigger: 'blur' },
    { min: 8, message: t('seller.passwordMin'), trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: t('seller.confirmPasswordRequired'), trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error(t('seller.passwordMismatch')))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}))

async function checkField(field, value) {
  if (!value) {
    fieldErrors[field] = ''
    return
  }
  try {
    const res = await checkApplyField({ field, value })
    const data = res.data || {}
    if (data.errors?.length) {
      fieldErrors[field] = data.errors[0]
      if (field === 'name') fieldWarnings.name = ''
    } else {
      fieldErrors[field] = ''
      if (field === 'name') {
        fieldWarnings.name = data.warnings?.[0] || ''
      }
    }
    formRef.value?.validateField(field)
  } catch {
    fieldErrors[field] = ''
  }
}

async function handleSubmit() {
  await formRef.value?.validate()
  if (fieldErrors.name || fieldErrors.contact_name || fieldErrors.contact_phone) {
    ElMessage.error(fieldErrors.name || fieldErrors.contact_name || fieldErrors.contact_phone)
    return
  }
  if (fieldWarnings.name) {
    try {
      await ElMessageBox.confirm(fieldWarnings.name, t('common.tip'), {
        type: 'warning',
        confirmButtonText: t('seller.applySubmit'),
        cancelButtonText: t('common.cancel'),
      })
    } catch {
      return
    }
  }
  loading.value = true
  try {
    await applyTenant({
      name: form.name,
      contact_name: form.contact_name,
      contact_phone: form.contact_phone,
      contact_email: form.contact_email,
      address: form.address,
      password: form.password,
    })
    await ElMessageBox.alert(t('seller.applySuccessMessage'), t('seller.applySuccessTitle'), {
      confirmButtonText: t('seller.applySuccessConfirm'),
      type: 'success',
      dangerouslyUseHTMLString: false,
    })
    router.push('/login')
  } catch (error) {
    ElMessage.error(error?.message || t('seller.applyFailed'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="apply-page">
    <div class="apply-card page-card">
      <div class="page-header">
        <h2>{{ t('seller.applyTitle') }}</h2>
        <router-link to="/login">{{ t('seller.hasAccount') }}</router-link>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" @submit.prevent="handleSubmit">
        <el-form-item :label="t('seller.shopName')" prop="name">
          <el-input
            v-model="form.name"
            :placeholder="t('seller.shopNamePlaceholder')"
            @blur="checkField('name', form.name)"
          />
          <div class="field-hint">{{ t('seller.shopNameHint') }}</div>
          <div v-if="fieldWarnings.name" class="field-warning">{{ fieldWarnings.name }}</div>
        </el-form-item>
        <el-form-item :label="t('seller.contact')" prop="contact_name">
          <el-input v-model="form.contact_name" @blur="checkField('contact_name', form.contact_name)" />
        </el-form-item>
        <el-form-item :label="t('seller.contactPhone')" prop="contact_phone">
          <el-input
            v-model="form.contact_phone"
            :placeholder="t('seller.phoneLoginTip')"
            @blur="checkField('contact_phone', form.contact_phone)"
          />
        </el-form-item>
        <el-form-item :label="t('seller.contactEmail')" prop="contact_email">
          <el-input v-model="form.contact_email" />
        </el-form-item>
        <el-form-item :label="t('seller.loginPassword')" prop="password">
          <el-input v-model="form.password" type="password" show-password :placeholder="t('seller.passwordMin')" />
        </el-form-item>
        <el-form-item :label="t('seller.confirmPassword')" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('seller.shopAddress')">
          <el-input v-model="form.address" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading">{{ t('seller.applySubmit') }}</el-button>
        </el-form-item>
        <p class="apply-tip">{{ t('seller.applyPendingTip') }}</p>
        <p class="apply-tip">{{ t('seller.codeAutoTip') }}</p>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.apply-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.apply-card {
  width: 560px;
  max-width: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.page-header a {
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
}

.apply-tip {
  margin: 0 0 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}

.field-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.field-warning {
  margin-top: 4px;
  font-size: 12px;
  color: #e6a23c;
  line-height: 1.5;
}
</style>
