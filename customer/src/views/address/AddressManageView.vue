<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { confirmDialog } from '@/utils/confirmDialog'
import AddressForm from '@/components/address/AddressForm.vue'
import {
  createAddress,
  deleteAddress,
  getAddresses,
  setDefaultAddress,
  updateAddress,
} from '@/api/address'
import { maskPhone } from '@/utils/region'

const router = useRouter()
const { t } = useI18n()

const addresses = ref([])
const loading = ref(true)
const showForm = ref(false)
const editingAddress = ref(null)
const saving = ref(false)

async function fetchAddresses() {
  loading.value = true
  try {
    const res = await getAddresses()
    addresses.value = res.data || []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingAddress.value = null
  showForm.value = true
}

function openEdit(addr) {
  editingAddress.value = { ...addr }
  showForm.value = true
}

async function handleSubmit(formData) {
  saving.value = true
  try {
    if (editingAddress.value?.id) {
      await updateAddress(editingAddress.value.id, formData)
      showToast(t('address.updateSuccess'))
    } else {
      await createAddress(formData)
      showToast(t('address.createSuccess'))
    }
    showForm.value = false
    editingAddress.value = null
    await fetchAddresses()
  } finally {
    saving.value = false
  }
}

async function handleDelete(addr) {
  try {
    await confirmDialog({
      title: t('address.deleteConfirmTitle'),
      message: t('address.deleteConfirmMessage'),
    })
    await deleteAddress(addr.id)
    showToast(t('address.deleteSuccess'))
    await fetchAddresses()
  } catch (error) {
    if (error !== 'cancel') {
      await fetchAddresses()
    }
  }
}

async function handleSetDefault(addr) {
  await setDefaultAddress(addr.id)
  showToast(t('address.defaultSuccess'))
  await fetchAddresses()
}

onMounted(fetchAddresses)
</script>

<template>
  <div class="address-page">
    <van-nav-bar
      :title="t('address.title')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <van-loading v-if="loading" class="page-loading" vertical>
      {{ t('common.loading') }}
    </van-loading>

    <template v-else>
      <div v-if="!addresses.length" class="empty-wrap">
        <van-empty :description="t('address.empty')" />
        <p class="empty-tip">{{ t('address.emptyTip') }}</p>
      </div>

      <div v-else class="address-list">
        <van-swipe-cell
          v-for="addr in addresses"
          :key="addr.id"
          class="address-swipe"
        >
          <div class="address-card" :class="{ default: addr.is_default }">
            <div class="address-head">
              <div class="address-user">
                <span class="address-name">{{ addr.name }}</span>
                <span class="address-phone">{{ maskPhone(addr.phone) }}</span>
              </div>
              <van-tag v-if="addr.is_default" type="primary" size="small">
                {{ t('checkout.defaultTag') }}
              </van-tag>
            </div>
            <div class="address-detail">
              {{ addr.province }} {{ addr.city }} {{ addr.district }} {{ addr.detail }}
            </div>
            <div class="address-actions">
              <van-button size="mini" plain @click="openEdit(addr)">{{ t('common.edit') }}</van-button>
              <van-button
                v-if="!addr.is_default"
                size="mini"
                plain
                type="primary"
                @click="handleSetDefault(addr)"
              >
                {{ t('address.setDefault') }}
              </van-button>
            </div>
          </div>
          <template #right>
            <van-button square type="danger" class="delete-btn" @click="handleDelete(addr)">
              {{ t('common.delete') }}
            </van-button>
          </template>
        </van-swipe-cell>
      </div>

      <div class="address-footer">
        <van-button type="primary" block round icon="plus" @click="openCreate">
          {{ t('address.add') }}
        </van-button>
      </div>
    </template>

    <AddressForm
      v-model="showForm"
      :initial-data="editingAddress"
      :saving="saving"
      @submit="handleSubmit"
    />
  </div>
</template>

<style scoped>
.address-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 88px;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.empty-wrap {
  padding: 40px 16px 0;
}

.empty-tip {
  margin-top: 8px;
  text-align: center;
  font-size: 13px;
  color: #969799;
}

.address-list {
  padding: 12px;
}

.address-swipe {
  margin-bottom: 10px;
  border-radius: 10px;
  overflow: hidden;
}

.address-card {
  padding: 14px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.address-card.default {
  border: 1px solid rgba(25, 137, 250, 0.35);
}

.address-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.address-user {
  display: flex;
  align-items: center;
  gap: 10px;
}

.address-name {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
}

.address-phone {
  font-size: 14px;
  color: #646566;
}

.address-detail {
  margin-top: 10px;
  font-size: 14px;
  color: #646566;
  line-height: 1.6;
}

.address-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.delete-btn {
  height: 100%;
  min-width: 72px;
}

.address-footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 12px 16px;
  background: #fff;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
}
</style>
