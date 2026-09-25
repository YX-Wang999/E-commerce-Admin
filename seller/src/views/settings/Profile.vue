<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { updateTenantProfile } from '@/api/auth'
import { uploadImage } from '@/api/upload'
import { resolveImageUrl } from '@/utils/media'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const saving = ref(false)
const logoUploading = ref(false)

const form = reactive({
  name: '',
  contact_name: '',
  contact_phone: '',
  contact_email: '',
  legal_person: '',
  business_license: '',
  address: '',
  description: '',
  logo: '',
})

const pendingFields = computed(() => authStore.tenant?.pending_fields || {})

const fieldLabels = computed(() => ({
  name: t('seller.shopName'),
  contact_name: t('seller.contact'),
  contact_phone: t('seller.contactPhone'),
  contact_email: t('seller.contactEmail'),
  legal_person: t('seller.legalPerson'),
  business_license: t('seller.businessLicense'),
}))

function isPending(field) {
  return Boolean(pendingFields.value[field])
}

function pendingHint(field) {
  if (!isPending(field)) return ''
  return t('seller.pendingReviewValue', { value: pendingFields.value[field] })
}

async function handleLogoUpload(options) {
  logoUploading.value = true
  try {
    const res = await uploadImage(options.file, 'brands')
    form.logo = res.data?.url || res.data?.path || ''
  } finally {
    logoUploading.value = false
  }
}

function syncForm() {
  const tenant = authStore.tenant
  if (!tenant) return
  form.name = tenant.name || ''
  form.contact_name = tenant.contact_name || ''
  form.contact_phone = tenant.contact_phone || ''
  form.contact_email = tenant.contact_email || ''
  form.legal_person = tenant.legal_person || ''
  form.business_license = tenant.business_license || ''
  form.address = tenant.address || ''
  form.description = tenant.description || ''
  form.logo = tenant.logo || ''
}

const isClosed = computed(() => authStore.tenant?.status === 'closed')

async function handleSubmit() {
  saving.value = true
  try {
    const res = await updateTenantProfile({ ...form })
    if (res.data?.tenant) {
      authStore.tenant = res.data.tenant
    } else {
      await authStore.fetchProfile()
    }
    syncForm()
    const pending = res.data?.pending_submitted || []
    const direct = res.data?.direct_updated || []
    if (pending.length) {
      ElMessage.warning(
        t('seller.pendingFieldsSubmitted', {
          fields: pending.map((f) => fieldLabels.value[f] || f).join('、'),
        }),
      )
    }
    if (direct.length) {
      ElMessage.success(t('common.success'))
    }
    if (!pending.length && !direct.length) {
      ElMessage.success(res.message || t('common.success'))
    }
  } catch (error) {
    ElMessage.error(error?.message || t('seller.saveFailed'))
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  if (!authStore.tenant) {
    await authStore.fetchProfile()
  }
  syncForm()
})
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>{{ t('seller.settings') }}</h2>
      <p class="sub-tip">{{ t('seller.settingsTip') }}</p>
    </div>

    <el-form ref="formRef" :model="form" label-width="110px" @submit.prevent="handleSubmit">
      <el-form-item :label="t('seller.tenantCode')">
        <el-input :model-value="authStore.tenant?.code" disabled />
      </el-form-item>

      <el-form-item :label="t('seller.shopName')">
        <el-input v-model="form.name" :disabled="isPending('name')" />
        <div v-if="isPending('name')" class="pending-tip">{{ pendingHint('name') }}</div>
      </el-form-item>

      <el-form-item :label="t('seller.contact')">
        <el-input v-model="form.contact_name" :disabled="isPending('contact_name')" />
        <div v-if="isPending('contact_name')" class="pending-tip">{{ pendingHint('contact_name') }}</div>
      </el-form-item>

      <el-form-item :label="t('seller.contactPhone')">
        <el-input v-model="form.contact_phone" :disabled="isPending('contact_phone')" />
        <div v-if="isPending('contact_phone')" class="pending-tip">{{ pendingHint('contact_phone') }}</div>
      </el-form-item>

      <el-form-item :label="t('seller.contactEmail')">
        <el-input v-model="form.contact_email" :disabled="isPending('contact_email')" />
        <div v-if="isPending('contact_email')" class="pending-tip">{{ pendingHint('contact_email') }}</div>
      </el-form-item>

      <el-form-item :label="t('seller.legalPerson')">
        <el-input v-model="form.legal_person" :disabled="isPending('legal_person')" />
        <div v-if="isPending('legal_person')" class="pending-tip">{{ pendingHint('legal_person') }}</div>
      </el-form-item>

      <el-form-item :label="t('seller.businessLicense')">
        <el-input
          v-model="form.business_license"
          :placeholder="t('seller.businessLicensePlaceholder')"
          :disabled="isPending('business_license')"
        />
        <div v-if="isPending('business_license')" class="pending-tip">{{ pendingHint('business_license') }}</div>
      </el-form-item>

      <el-form-item :label="t('seller.shopAddress')">
        <el-input v-model="form.address" type="textarea" :rows="2" />
      </el-form-item>

      <el-form-item :label="t('seller.shopDescription')">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          :placeholder="t('seller.shopDescriptionPlaceholder')"
        />
      </el-form-item>

      <el-form-item :label="t('seller.logoUrl')">
        <div class="logo-field">
          <el-upload :show-file-list="false" :http-request="handleLogoUpload" accept="image/*">
            <el-button :loading="logoUploading">{{ t('seller.uploadImage') }}</el-button>
          </el-upload>
          <el-image v-if="form.logo" :src="resolveImageUrl(form.logo)" fit="cover" class="logo-preview" />
          <el-input v-model="form.logo" :placeholder="t('seller.logoPlaceholder')" />
        </div>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" native-type="submit" :loading="saving">{{ t('seller.saveSettings') }}</el-button>
      </el-form-item>
    </el-form>

    <div v-if="!isClosed" class="danger-zone">
      <h3>{{ t('seller.dangerZone') }}</h3>
      <p>{{ t('seller.closeShopTip') }}</p>
      <el-button type="danger" plain @click="router.push({ name: 'SettingsClosure' })">
        {{ t('seller.closeShop') }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.sub-tip {
  margin: 8px 0 0;
  font-size: 13px;
  color: #909399;
}

.pending-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #e6a23c;
}

.logo-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.logo-preview {
  width: 72px;
  height: 72px;
  border-radius: 8px;
}

.danger-zone {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

.danger-zone h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #f56c6c;
}

.danger-zone p {
  margin: 0 0 16px;
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
}
</style>
