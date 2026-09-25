<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown } from '@element-plus/icons-vue'
import { useLocaleStore } from '@/stores/locale'

defineProps({
  compact: {
    type: Boolean,
    default: false,
  },
})

const { t } = useI18n()
const localeStore = useLocaleStore()

const currentLocaleLabel = computed(() => {
  const option = localeStore.localeOptions.find((item) => item.value === localeStore.locale)
  return option?.label || t('locale.label')
})

function handleLocaleChange(value) {
  localeStore.setLocale(value)
}
</script>

<template>
  <el-dropdown trigger="click" @command="handleLocaleChange">
    <el-button text :class="{ 'locale-btn': !compact, 'locale-btn-compact': compact }">
      <span v-if="!compact" class="locale-icon">🌐</span>
      <span class="locale-label">{{ currentLocaleLabel }}</span>
      <el-icon class="el-icon--right"><ArrowDown /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="item in localeStore.localeOptions"
          :key="item.value"
          :command="item.value"
          :class="{ 'is-active': item.value === localeStore.locale }"
        >
          {{ item.label }}
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<style scoped>
.locale-btn,
.locale-btn-compact {
  color: inherit;
}

.locale-icon {
  margin-right: 4px;
}

.locale-label {
  font-size: 14px;
}
</style>
