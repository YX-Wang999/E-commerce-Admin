import { createI18n, useI18n } from 'vue-i18n'
import zhCN from '@/i18n/locales/zh-CN.js'
import enUS from '@/i18n/locales/en-US.js'
import jaJP from '@/i18n/locales/ja-JP.js'
import { resolveMenuLabel } from '@/i18n/menu'

export const LOCALE_STORAGE_KEY = 'seller_locale'
export const DEFAULT_LOCALE = 'zh-CN'
export const FALLBACK_LOCALE = 'zh-CN'

export const LOCALE_OPTIONS = [
  { value: 'zh-CN', labelKey: 'locale.zhCN' },
  { value: 'en-US', labelKey: 'locale.enUS' },
  { value: 'ja-JP', labelKey: 'locale.jaJP' },
]

function getInitialLocale() {
  const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (saved && LOCALE_OPTIONS.some((item) => item.value === saved)) {
    return saved
  }
  const browserLang = navigator.language
  if (browserLang.startsWith('en')) return 'en-US'
  if (browserLang.startsWith('ja')) return 'ja-JP'
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

export function setLocale(locale) {
  if (!LOCALE_OPTIONS.some((item) => item.value === locale)) return
  i18n.global.locale.value = locale
  localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  document.documentElement.lang = locale
}

export function useMenuTitle() {
  const { t, te } = useI18n()
  return (path, fallbackTitle = '') => resolveMenuLabel(t, te, path, fallbackTitle)
}

export default i18n
