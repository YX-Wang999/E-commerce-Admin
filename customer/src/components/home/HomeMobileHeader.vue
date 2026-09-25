<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { HOME_CHANNEL_TABS } from '@/constants/homeChannels'

const props = defineProps({
  activeChannel: {
    type: String,
    default: 'recommend',
  },
})

const emit = defineEmits(['update:activeChannel', 'select-channel'])

const router = useRouter()
const { t } = useI18n()
const keyword = ref('')
const scrollRef = ref(null)
const tabRefs = ref({})
const indicatorStyle = ref({ opacity: 0 })

const channelTabs = HOME_CHANNEL_TABS

function setTabRef(key, el) {
  if (el) {
    tabRefs.value[key] = el
  }
}

function selectChannel(tab) {
  emit('update:activeChannel', tab.key)
  emit('select-channel', tab.key)
}

function updateIndicator() {
  nextTick(() => {
    const scrollEl = scrollRef.value
    const tabEl = tabRefs.value[props.activeChannel]
    if (!scrollEl || !tabEl) return

    const scrollRect = scrollEl.getBoundingClientRect()
    const tabRect = tabEl.getBoundingClientRect()
    indicatorStyle.value = {
      width: `${tabRect.width}px`,
      transform: `translateX(${tabRect.left - scrollRect.left + scrollEl.scrollLeft}px)`,
      opacity: 1,
    }

    tabEl.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' })
  })
}

function goSearchPage() {
  router.push({
    name: 'Search',
    query: keyword.value.trim() ? { keyword: keyword.value.trim() } : {},
  })
}

function submitSearch() {
  goSearchPage()
}

function onScan() {
  showToast(t('home.scanDeveloping'))
}

function onCameraSearch() {
  showToast(t('home.cameraSearchDeveloping'))
}

watch(() => props.activeChannel, updateIndicator)
onMounted(updateIndicator)
</script>

<template>
  <header class="home-mobile-header">
    <div class="channel-nav">
      <div ref="scrollRef" class="channel-nav__scroll">
        <span class="channel-nav__indicator" :style="indicatorStyle" aria-hidden="true" />
        <button
          v-for="tab in channelTabs"
          :key="tab.key"
          :ref="(el) => setTabRef(tab.key, el)"
          type="button"
          class="channel-tab"
          :class="{ active: activeChannel === tab.key, 'channel-tab--sticky': tab.sticky && activeChannel === tab.key }"
          @click="selectChannel(tab)"
        >
          {{ t(tab.labelKey) }}
        </button>
      </div>
    </div>

    <div class="search-nav">
      <button type="button" class="search-nav__icon" :aria-label="t('home.scan')" @click="onScan">
        <van-icon name="scan" size="22" />
      </button>
      <div class="search-nav__input" @click="goSearchPage">
        <input
          v-model="keyword"
          type="search"
          class="search-input"
          :placeholder="t('home.searchPlaceholder')"
          @keyup.enter="submitSearch"
          @click.stop
        />
      </div>
      <button
        type="button"
        class="search-nav__icon"
        :aria-label="t('home.cameraSearch')"
        @click="onCameraSearch"
      >
        <van-icon name="photograph" size="22" />
      </button>
      <button type="button" class="search-nav__btn" @click="submitSearch">
        {{ t('home.searchAction') }}
      </button>
    </div>
  </header>
</template>

<style scoped>
.home-mobile-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.channel-nav {
  height: 44px;
  border-bottom: 1px solid #f5f5f5;
}

.channel-nav__scroll {
  position: relative;
  display: flex;
  align-items: stretch;
  height: 100%;
  overflow-x: auto;
  padding: 0 8px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.channel-nav__scroll::-webkit-scrollbar {
  display: none;
}

.channel-nav__indicator {
  position: absolute;
  left: 0;
  bottom: 5px;
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(90deg, #ff7875, var(--color-primary, #ff4d4f));
  transition:
    transform 0.32s cubic-bezier(0.32, 0.72, 0, 1),
    width 0.28s cubic-bezier(0.32, 0.72, 0, 1),
    opacity 0.2s;
  pointer-events: none;
  z-index: 1;
}

.channel-tab {
  flex-shrink: 0;
  padding: 0 14px;
  border: none;
  background: transparent;
  font-size: 15px;
  color: #666;
  cursor: pointer;
  white-space: nowrap;
  position: relative;
  transition:
    color 0.25s ease,
    transform 0.15s ease,
    font-size 0.25s ease;
  -webkit-tap-highlight-color: transparent;
}

.channel-tab--sticky {
  position: sticky;
  left: 0;
  z-index: 2;
  background: #fff;
  box-shadow: 6px 0 8px -4px rgba(0, 0, 0, 0.06);
}

.channel-tab:active {
  transform: scale(0.92);
}

.channel-tab.active {
  color: var(--color-primary, #ff4d4f);
  font-weight: 700;
  font-size: 17px;
}

.search-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 10px;
}

.search-nav__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #333;
  cursor: pointer;
  flex-shrink: 0;
}

.search-nav__input {
  flex: 1;
  min-width: 0;
  height: 34px;
  padding: 0 12px;
  background: #f5f5f5;
  border-radius: 17px;
  display: flex;
  align-items: center;
}

.search-input {
  width: 100%;
  border: none;
  background: transparent;
  font-size: 14px;
  color: #333;
  outline: none;
}

.search-input::placeholder {
  color: #969799;
}

.search-nav__btn {
  flex-shrink: 0;
  height: 34px;
  padding: 0 14px;
  border: none;
  border-radius: 17px;
  background: var(--color-primary, #ff4d4f);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
</style>
