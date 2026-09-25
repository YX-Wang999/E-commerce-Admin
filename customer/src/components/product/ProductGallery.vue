<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMediaQuery } from '@vueuse/core'
import { showImagePreview } from 'vant'

const props = defineProps({
  images: {
    type: Array,
    default: () => [],
  },
  productName: {
    type: String,
    default: '',
  },
})

const { t } = useI18n()
const isDesktop = useMediaQuery('(min-width: 769px)')

const currentIndex = ref(0)
const isHovering = ref(false)
const imageLoaded = ref(false)
const mainImage = ref(null)

const glassSize = 120
const resultSize = 400
const mouse = reactive({ x: 0, y: 0 })
const imageRender = reactive({ width: 0, height: 0, offsetX: 0, offsetY: 0 })

const displayImages = computed(() => props.images.filter(Boolean))
const currentImage = computed(() => displayImages.value[currentIndex.value] || '')

const zoom = computed(() => resultSize / glassSize)

const glassLeft = computed(() => {
  const relX = mouse.x - imageRender.offsetX
  const max = Math.max(imageRender.width - glassSize, 0)
  return imageRender.offsetX + Math.max(0, Math.min(relX - glassSize / 2, max))
})

const glassTop = computed(() => {
  const relY = mouse.y - imageRender.offsetY
  const max = Math.max(imageRender.height - glassSize, 0)
  return imageRender.offsetY + Math.max(0, Math.min(relY - glassSize / 2, max))
})

const glassStyle = computed(() => ({
  left: `${glassLeft.value}px`,
  top: `${glassTop.value}px`,
  width: `${glassSize}px`,
  height: `${glassSize}px`,
}))

const resultStyle = computed(() => {
  const scale = zoom.value
  const relGlassLeft = glassLeft.value - imageRender.offsetX
  const relGlassTop = glassTop.value - imageRender.offsetY
  return {
    width: `${resultSize}px`,
    height: `${resultSize}px`,
    backgroundImage: currentImage.value ? `url(${currentImage.value})` : 'none',
    backgroundSize: `${imageRender.width * scale}px ${imageRender.height * scale}px`,
    backgroundPosition: `-${relGlassLeft * scale}px -${relGlassTop * scale}px`,
    backgroundRepeat: 'no-repeat',
  }
})

const showMagnifier = computed(
  () => isDesktop.value && isHovering.value && imageLoaded.value && Boolean(currentImage.value),
)

function syncImageRenderRect() {
  const el = mainImage.value
  if (!el) return
  const cw = el.clientWidth
  const ch = el.clientHeight
  const nw = el.naturalWidth || cw
  const nh = el.naturalHeight || ch
  const scale = Math.min(cw / nw, ch / nh)
  imageRender.width = nw * scale
  imageRender.height = nh * scale
  imageRender.offsetX = (cw - imageRender.width) / 2
  imageRender.offsetY = (ch - imageRender.height) / 2
}

function isInsideImage(localX, localY) {
  return (
    localX >= imageRender.offsetX
    && localX <= imageRender.offsetX + imageRender.width
    && localY >= imageRender.offsetY
    && localY <= imageRender.offsetY + imageRender.height
  )
}

function handleMouseMove(event) {
  if (!isDesktop.value) return
  const rect = mainImage.value?.getBoundingClientRect()
  if (!rect) return
  syncImageRenderRect()
  const localX = event.clientX - rect.left
  const localY = event.clientY - rect.top
  if (!isInsideImage(localX, localY)) {
    isHovering.value = false
    return
  }
  mouse.x = localX
  mouse.y = localY
  isHovering.value = true
}

function handleMouseLeave() {
  isHovering.value = false
}

function handleImageLoad() {
  imageLoaded.value = true
  syncImageRenderRect()
}

function selectImage(index) {
  currentIndex.value = index
}

function prevImage() {
  if (displayImages.value.length <= 1) return
  currentIndex.value =
    (currentIndex.value - 1 + displayImages.value.length) % displayImages.value.length
}

function nextImage() {
  if (displayImages.value.length <= 1) return
  currentIndex.value = (currentIndex.value + 1) % displayImages.value.length
}

function openPreview() {
  if (!displayImages.value.length) return
  showImagePreview({
    images: displayImages.value,
    startPosition: currentIndex.value,
    closeable: true,
  })
}

watch(currentIndex, () => {
  imageLoaded.value = false
})

watch(
  () => props.images,
  () => {
    currentIndex.value = 0
    imageLoaded.value = false
  },
)
</script>

<template>
  <div class="product-gallery">
    <div v-if="!isDesktop" class="gallery-mobile">
      <van-swipe
        v-if="displayImages.length"
        class="gallery-swipe"
        indicator-color="#fff"
        :autoplay="displayImages.length > 1 ? 4000 : 0"
        @change="(index) => (currentIndex = index)"
      >
        <van-swipe-item v-for="(img, index) in displayImages" :key="`${img}-${index}`">
          <van-image class="gallery-swipe__image" :src="img" fit="contain" @click="openPreview">
            <template #loading>
              <van-skeleton-image class="gallery-swipe__skeleton" />
            </template>
            <template #error>
              <div class="gallery-empty">{{ t('common.noImage') }}</div>
            </template>
          </van-image>
        </van-swipe-item>
      </van-swipe>
      <div v-else class="gallery-empty gallery-empty--block">{{ t('common.noImage') }}</div>
    </div>

    <div v-else class="gallery-desktop">
      <div class="gallery-stage">
        <div
          class="gallery-main"
          @mousemove="handleMouseMove"
          @mouseleave="handleMouseLeave"
        >
          <img
            v-if="currentImage"
            ref="mainImage"
            class="gallery-main__image"
            :src="currentImage"
            :alt="productName"
            @load="handleImageLoad"
            @click="openPreview"
          />
          <div v-else class="gallery-empty">{{ t('common.noImage') }}</div>

          <button
            v-if="displayImages.length > 1"
            type="button"
            class="gallery-nav gallery-nav--prev"
            :aria-label="t('product.prevImage')"
            @click.stop="prevImage"
          >
            <van-icon name="arrow-left" />
          </button>
          <button
            v-if="displayImages.length > 1"
            type="button"
            class="gallery-nav gallery-nav--next"
            :aria-label="t('product.nextImage')"
            @click.stop="nextImage"
          >
            <van-icon name="arrow-right" />
          </button>

          <div
            class="magnifier-glass"
            :class="{ visible: showMagnifier }"
            :style="glassStyle"
          />
        </div>

        <div
          class="magnifier-result"
          :class="{ visible: showMagnifier }"
          :style="resultStyle"
        />
      </div>

      <div v-if="displayImages.length > 1" class="thumbnail-list">
        <button
          v-for="(img, index) in displayImages"
          :key="`${img}-${index}`"
          type="button"
          class="thumbnail-item"
          :class="{ active: index === currentIndex }"
          @click="selectImage(index)"
        >
          <img :src="img" :alt="productName" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.product-gallery {
  width: 100%;
}

.gallery-mobile {
  width: 100%;
}

.gallery-swipe {
  width: 100%;
  height: 100vw;
  max-height: 420px;
  background: #fff;
}

.gallery-swipe__image,
.gallery-swipe__skeleton,
.gallery-swipe__image :deep(.van-image__img) {
  width: 100%;
  height: 100%;
}

.gallery-swipe__skeleton,
.gallery-swipe__skeleton :deep(.van-skeleton-image) {
  width: 100%;
  height: 100%;
}

.gallery-desktop {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
}

.gallery-stage {
  position: relative;
  width: 400px;
  height: 400px;
  flex-shrink: 0;
}

.gallery-main {
  position: relative;
  width: 400px;
  height: 400px;
  border-radius: 12px;
  overflow: hidden;
  background: #f5f6fa;
  cursor: crosshair;
}

.gallery-main__image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  background: #fff;
}

.gallery-nav {
  position: absolute;
  top: 50%;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: #323233;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transform: translateY(-50%);
  cursor: pointer;
}

.gallery-nav--prev {
  left: 12px;
}

.gallery-nav--next {
  right: 12px;
}

.magnifier-glass {
  position: absolute;
  z-index: 3;
  border: 2px solid #1989fa;
  background: rgba(25, 137, 250, 0.12);
  pointer-events: none;
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.magnifier-glass.visible {
  opacity: 1;
}

.magnifier-result {
  position: absolute;
  left: calc(100% + 16px);
  top: 0;
  z-index: 5;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  background-color: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.magnifier-result.visible {
  opacity: 1;
}

.thumbnail-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 400px;
}

.thumbnail-item {
  width: 60px;
  height: 60px;
  padding: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid transparent;
  background: #fff;
  cursor: pointer;
}

.thumbnail-item.active {
  border-color: #1989fa;
}

.thumbnail-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.gallery-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #969799;
  background: #f5f6fa;
}

.gallery-empty--block {
  min-height: 240px;
}

@media (max-width: 1100px) {
  .magnifier-result {
    display: none;
  }
}
</style>
