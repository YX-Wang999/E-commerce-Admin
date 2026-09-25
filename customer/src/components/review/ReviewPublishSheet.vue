<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { createReview, followUpReview, uploadReviewImage } from '@/api/review'
import { resolveErrorMessage, toastSuccess } from '@/utils/feedback'
import { resolveImageUrl } from '@/utils/product'

const props = defineProps({
  show: { type: Boolean, default: false },
  mode: { type: String, default: 'create' },
  target: { type: Object, default: null },
  reviewId: { type: [Number, String], default: null },
})

const emit = defineEmits(['update:show', 'success'])

const { t } = useI18n()
const rating = ref(5)
const content = ref('')
const images = ref([])
const isAnonymous = ref(false)
const allowComment = ref(true)
const submitting = ref(false)
const uploading = ref(false)

const visible = ref(false)
watch(() => props.show, (v) => { visible.value = v; if (v) resetForm() }, { immediate: true })
watch(visible, (v) => emit('update:show', v))

function resetForm() {
  rating.value = 5
  content.value = ''
  images.value = []
  isAnonymous.value = false
  allowComment.value = true
}

async function afterRead(file) {
  uploading.value = true
  try {
    const blob = file.file || file
    const res = await uploadReviewImage(blob)
    images.value.push(res.data.url)
  } catch {
    showToast(t('review.uploadFailed'))
  } finally {
    uploading.value = false
  }
}

function removeImage(index) {
  images.value.splice(index, 1)
}

async function handleSubmit() {
  if (!content.value.trim()) {
    showToast(t('review.contentRequired'))
    return
  }
  submitting.value = true
  try {
    if (props.mode === 'follow_up' && props.reviewId) {
      const res = await followUpReview(props.reviewId, {
        content: content.value.trim(),
        images: images.value,
      })
      toastSuccess(res.message || t('review.followUpSuccess'))
    } else if (props.target) {
      const res = await createReview({
        product_id: props.target.product_id,
        order_id: props.target.order_id,
        rating: rating.value,
        content: content.value.trim(),
        images: images.value,
        is_anonymous: isAnonymous.value,
        allow_comment: allowComment.value,
      })
      toastSuccess(res.message || t('review.submitSuccess'))
    }
    visible.value = false
    emit('success')
  } catch (error) {
    showToast(resolveErrorMessage(error, 'review.submitFailed'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <van-popup v-model:show="visible" round position="bottom" :style="{ maxHeight: '90vh' }">
    <div class="publish-sheet">
      <div class="sheet-title">
        {{ mode === 'follow_up' ? t('review.followUpTitle') : t('review.publishTitle') }}
      </div>
      <div v-if="target && mode === 'create'" class="product-row">
        <img v-if="target.product_image" :src="resolveImageUrl(target.product_image)" alt="" class="thumb" />
        <div>
          <div class="product-name">{{ target.product_name }}</div>
          <div class="order-no">{{ t('checkout.orderNo', { no: target.order_no }) }}</div>
        </div>
      </div>
      <div v-if="mode === 'create'" class="rate-row">
        <van-rate v-model="rating" :size="24" color="#ee0a24" />
      </div>
      <van-field
        v-model="content"
        rows="4"
        autosize
        type="textarea"
        maxlength="500"
        show-word-limit
        :placeholder="t('review.contentPlaceholder')"
      />
      <van-uploader
        :after-read="afterRead"
        :max-count="6"
        :disabled="uploading"
        accept="image/*"
      />
      <div v-if="images.length" class="preview-row">
        <div v-for="(img, idx) in images" :key="img" class="preview-item">
          <img :src="resolveImageUrl(img)" alt="" />
          <van-icon name="cross" class="remove" @click="removeImage(idx)" />
        </div>
      </div>
      <template v-if="mode === 'create'">
        <van-checkbox v-model="isAnonymous" shape="square">{{ t('review.anonymous') }}</van-checkbox>
        <van-checkbox v-model="allowComment" shape="square">{{ t('review.allowComment') }}</van-checkbox>
      </template>
      <van-button type="primary" block round :loading="submitting" @click="handleSubmit">
        {{ t('review.submit') }}
      </van-button>
    </div>
  </van-popup>
</template>

<style scoped>
.publish-sheet {
  padding: 16px 16px calc(16px + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sheet-title {
  font-size: 17px;
  font-weight: 600;
  text-align: center;
}

.product-row {
  display: flex;
  gap: 10px;
  padding: 10px;
  background: #f7f8fa;
  border-radius: 8px;
}

.thumb {
  width: 56px;
  height: 56px;
  border-radius: 6px;
  object-fit: cover;
}

.product-name {
  font-size: 14px;
  font-weight: 600;
}

.order-no {
  font-size: 12px;
  color: #969799;
  margin-top: 4px;
}

.rate-row {
  display: flex;
  justify-content: center;
  padding: 4px 0;
}

.preview-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-item {
  position: relative;
  width: 72px;
  height: 72px;
}

.preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
}

.remove {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #fff;
  border-radius: 50%;
  padding: 2px;
}
</style>
