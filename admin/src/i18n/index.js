/** vue-i18n setup and helpers. */

import { createI18n, useI18n } from 'vue-i18n'
import enUS from '@/i18n/locales/en-US'
import zhCN from '@/i18n/locales/zh-CN'
import jaJP from '@/i18n/locales/ja-JP'
import { resolveMenuLabel } from '@/i18n/menu'

export { pathToMenuKey, formatPathFallback, resolveMenuLabel } from '@/i18n/menu'

export const LOCALE_STORAGE_KEY = 'admin_locale'
export const DEFAULT_LOCALE = 'zh-CN'
export const FALLBACK_LOCALE = 'zh-CN'

export const LOCALE_OPTIONS = [
  { value: 'zh-CN', labelKey: 'locale.zhCN' },
  { value: 'en-US', labelKey: 'locale.enUS' },
  { value: 'ja-JP', labelKey: 'locale.jaJP' },
]

function getInitialLocale() {
  const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (saved && ['zh-CN', 'en-US', 'ja-JP'].includes(saved)) {
    return saved
  }
  const browserLang = navigator.language
  if (browserLang.startsWith('en')) {
    return 'en-US'
  }
  if (browserLang.startsWith('ja')) {
    return 'ja-JP'
  }
  return DEFAULT_LOCALE
}

const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: FALLBACK_LOCALE,
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
    'ja-JP': jaJP,
  },
})

export function translateMenuTitle(path, fallbackTitle = '') {
  return resolveMenuLabel(
    i18n.global.t.bind(i18n.global),
    i18n.global.te.bind(i18n.global),
    path,
    fallbackTitle,
  )
}

/** Reactive menu title helper — use inside setup / script setup. */
export function useMenuTitle() {
  const { t, te } = useI18n()

  function translateMenuTitleReactive(path, fallbackTitle = '') {
    return resolveMenuLabel(t, te, path, fallbackTitle)
  }

  return translateMenuTitleReactive
}

export function translateDashboardCard(key, fallbackLabel = '') {
  if (key && i18n.global.te(`dashboard.cards.${key}`)) {
    return i18n.global.t(`dashboard.cards.${key}`)
  }
  return fallbackLabel
}

export function translateInventoryType(type, fallbackLabel = '') {
  if (type && i18n.global.te(`inventoryType.${type}`)) {
    return i18n.global.t(`inventoryType.${type}`)
  }
  return fallbackLabel
}

export function translateActivationStatus(status, fallbackLabel = '') {
  const keyMap = {
    none: 'system.user.activationStatusNone',
    pending: 'system.user.activationStatusPending',
    activated: 'system.user.activationStatusActivated',
    expired: 'system.user.activationStatusExpired',
    failed: 'system.user.activationStatusFailed',
  }
  const key = keyMap[status]
  if (key && i18n.global.te(key)) {
    return i18n.global.t(key)
  }
  return fallbackLabel
}

export default i18n
