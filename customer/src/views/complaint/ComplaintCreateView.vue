<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { getOrder } from '@/api/order'
import { createComplaint, uploadComplaintImage } from '@/api/complaint'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const order = ref(null)
const loading = ref(true)
const submitting = ref(false)
const category = ref('product_quality')
const title = ref('')
const content = ref('')
const attachments = ref([])
const uploading = ref(false)

const categoryOptions = computed(() => [
  { text: t('complaint.categoryProductQuality'), value: 'product_quality' },
  { text: t('complaint.categoryShipping'), value: 'shipping' },
  { text: t('complaint.categoryService'), value: 'service' },
  { text: t('complaint.categoryFraud'), value: 'fraud' },
  { text: t('complaint.categoryRefund'), value: 'refund' },
  { text: t('complaint.categoryOther'), value: 'other' },
])

function orderShopName(item) {
  if (!item) return t('order.platformShop')
  if (item.tenant_name) return item.tenant_name
  if (item.tenant?.name) return item.tenant.name
  return t('order.platformShop')
}

async function fetchOrder() {
  loading.value = true
  try {
    const res = await getOrder(route.query.order_id)
    order.value = res.data
  } catch {
    order.value = null
  } finally {
    loading.value = false
  }
}

async function afterRead(file) {
  uploading.value = true
  try {
    const blob = file.file || file
    const res = await uploadComplaintImage(blob)
    attachments.value.push(res.data.url)
  } catch {
    showToast(t('complaint.uploadFailed'))
  } finally {
    uploading.value = false
  }
}

function removeAttachment(index) {
  attachments.value.splice(index, 1)
}

async function handleSubmit() {
  if (!order.value?.tenant) {
    showToast(t('complaint.invalidOrder'))
    return
  }
  if (!title.value.trim() || !content.value.trim()) {
    showToast(t('complaint.fillRequired'))
    return
  }
  submitting.value = true
  try {
    const tenantId = order.value.tenant?.id ?? order.value.tenant
    const res = await createComplaint({
      tenant_id: tenantId,
      order_id: order.value.id,
      category: category.value,
      title: title.value.trim(),
      content: content.value.trim(),
      attachments: attachments.value,
    })
    showToast(t('complaint.submitSuccess'))
    router.replace({ name: 'ComplaintDetail', params: { id: res.data.id } })
  } catch {
    // handled by interceptor
  } finally {
    submitting.value = false
  }
}

onMounted(fetchOrder)
</script>

<template>
  <div class="complaint-create-page">
    <van-nav-bar :title="t('complaint.createTitle')" left-arrow @click-left="router.back()" />

    <van-loading v-if="loading" class="page-loading" />
    <van-empty v-else-if="!order" :description="t('complaint.invalidOrder')" />

    <template v-else>
      <div class="order-card">
        <div>{{ t('complaint.orderNo', { no: order.order_no }) }}</div>
        <div class="shop">{{ t('order.shop') }}：{{ orderShopName(order) }}</div>
      </div>

      <van-cell-group inset>
        <van-field :label="t('complaint.category')">
          <template #input>
            <select v-model="category" class="native-select">
              <option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">
                {{ opt.text }}
              </option>
            </select>
          </template>
        </van-field>
        <van-field
          v-model="title"
          :label="t('complaint.titleLabel')"
          maxlength="200"
          :placeholder="t('complaint.titlePlaceholder')"
        />
        <van-field
          v-model="content"
          rows="4"
          autosize
          type="textarea"
          maxlength="2000"
          :label="t('complaint.contentLabel')"
          :placeholder="t('complaint.contentPlaceholder')"
        />
      </van-cell-group>

      <div class="upload-block">
        <div class="upload-title">{{ t('complaint.attachments') }}</div>
        <van-uploader :after-read="afterRead" :disabled="uploading" accept="image/*" />
        <div v-if="attachments.length" class="attachment-list">
          <a v-for="(url, index) in attachments" :key="url" :href="url" target="_blank" rel="noopener">
            {{ t('complaint.attachment', { n: index + 1 }) }}
          </a>
          <van-button size="mini" @click="removeAttachment(attachments.length - 1)">
            {{ t('complaint.removeLast') }}
          </van-button>
        </div>
      </div>

      <div class="footer">
        <van-button type="primary" block :loading="submitting" @click="handleSubmit">
          {{ t('complaint.submit') }}
        </van-button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.complaint-create-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 80px;
}
.page-loading {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}
.order-card {
  margin: 12px 16px;
  padding: 12px 14px;
  background: #fff;
  border-radius: 10px;
  font-size: 14px;
}
.shop {
  margin-top: 4px;
  color: #969799;
  font-size: 12px;
}
.native-select {
  width: 100%;
  border: none;
  background: transparent;
  font-size: 14px;
}
.upload-block {
  margin: 12px 16px;
  padding: 12px 14px;
  background: #fff;
  border-radius: 10px;
}
.upload-title {
  margin-bottom: 8px;
  font-size: 14px;
}
.attachment-list {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 12px 16px;
  background: #fff;
}
</style>
