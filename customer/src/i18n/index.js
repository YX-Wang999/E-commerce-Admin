/** Customer mall vue-i18n setup. */

import { createI18n } from 'vue-i18n'
import { Locale } from 'vant'
import vantZhCN from 'vant/es/locale/lang/zh-CN'
import vantEnUS from 'vant/es/locale/lang/en-US'
import vantJaJP from 'vant/es/locale/lang/ja-JP'
import zhCN from '@/i18n/locales/zh-CN'
import enUS from '@/i18n/locales/en-US'
import jaJP from '@/i18n/locales/ja-JP'

export const LOCALE_STORAGE_KEY = 'customer_locale'
export const DEFAULT_LOCALE = 'zh-CN'
export const FALLBACK_LOCALE = 'zh-CN'

export const LOCALE_OPTIONS = [
  { value: 'zh-CN', labelKey: 'locale.zhCN' },
  { value: 'en-US', labelKey: 'locale.enUS' },
  { value: 'ja-JP', labelKey: 'locale.jaJP' },
]

const VANT_LOCALE_MAP = {
  'zh-CN': vantZhCN,
  'en-US': vantEnUS,
  'ja-JP': vantJaJP,
}

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

export function applyVantLocale(locale) {
  Locale.use(VANT_LOCALE_MAP[locale] || vantZhCN)
}

const initialLocale = getInitialLocale()
applyVantLocale(initialLocale)
document.documentElement.lang = initialLocale

const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
  fallbackLocale: FALLBACK_LOCALE,
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
    'ja-JP': jaJP,
  },
})

export function setLocale(locale) {
  if (!LOCALE_OPTIONS.some((item) => item.value === locale)) {
    return
  }
  i18n.global.locale.value = locale
  localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  applyVantLocale(locale)
  document.documentElement.lang = locale
}

export function getLocale() {
  return i18n.global.locale.value
}

export default i18n
