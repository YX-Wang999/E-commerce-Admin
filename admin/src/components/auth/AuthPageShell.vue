<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown } from '@element-plus/icons-vue'
import { APP_COPYRIGHT, APP_VERSION } from '@/config/app'
import { useLocaleStore } from '@/stores/locale'

defineProps({
  title: {
    type: String,
    default: '',
  },
})

const { t } = useI18n()
const localeStore = useLocaleStore()

const currentLocaleLabel = computed(() => {
  const option = localeStore.localeOptions.find((item) => item.value === localeStore.locale)
  return option?.label || t('login.language')
})

function handleLocaleChange(value) {
  localeStore.setLocale(value)
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-locale">
      <el-dropdown trigger="click" @command="handleLocaleChange">
        <button type="button" class="locale-switch" :aria-label="t('login.language')">
          <span class="locale-switch__icon">🌐</span>
          <span class="locale-switch__label">{{ currentLocaleLabel }}</span>
          <el-icon class="locale-switch__arrow"><ArrowDown /></el-icon>
        </button>
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
    </div>

    <div class="auth-shell">
      <div class="auth-card">
        <h2 v-if="title" class="auth-title">{{ title }}</h2>
        <slot />
      </div>

      <footer class="auth-footer">
        <span>{{ APP_COPYRIGHT }}</span>
        <span class="auth-footer__version">{{ APP_VERSION }}</span>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  padding: 24px 16px;
}

.auth-locale {
  position: absolute;
  top: 24px;
  right: 24px;
  z-index: 2;
}

.locale-switch {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid rgba(255, 255, 255, 0.75);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  color: #303133;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.locale-switch:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.16);
}

.locale-switch__icon {
  font-size: 16px;
  line-height: 1;
}

.locale-switch__label {
  max-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.locale-switch__arrow {
  color: #909399;
}

.auth-shell {
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.auth-card {
  width: 100%;
  padding: 36px 32px 28px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.16);
}

.auth-title {
  margin: 0 0 24px;
  text-align: center;
  font-size: 24px;
  color: #303133;
}

.auth-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.88);
  font-size: 13px;
}

.auth-footer__version {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
}

:deep(.el-dropdown-menu__item.is-active) {
  color: var(--el-color-primary);
  font-weight: 600;
}

@media (max-width: 575px) {
  .auth-locale {
    top: 16px;
    right: 16px;
  }

  .locale-switch {
    padding: 8px 12px;
  }

  .locale-switch__label {
    max-width: 72px;
  }

  .auth-card {
    padding: 28px 20px 22px;
  }

  .auth-footer {
    flex-direction: column;
    gap: 6px;
  }
}
</style>
