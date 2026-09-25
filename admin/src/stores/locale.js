import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import enUS from 'element-plus/dist/locale/en.mjs'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import ja from 'element-plus/dist/locale/ja.mjs'
import i18n, { LOCALE_OPTIONS, LOCALE_STORAGE_KEY } from '@/i18n'
import { setBaseTitle } from '@shared/utils/titleAlert.js'

const ELEMENT_LOCALE_MAP = {
  'zh-CN': zhCn,
  'en-US': enUS,
  'ja-JP': ja,
}

const HTML_LANG_MAP = {
  'zh-CN': 'zh-CN',
  'en-US': 'en',
  'ja-JP': 'ja',
}

function applyDocumentLang(code) {
  document.documentElement.lang = HTML_LANG_MAP[code] || 'en'
}

function applyDocumentTitle() {
  setBaseTitle(i18n.global.t('layout.siteTitle'))
}

export const useLocaleStore = defineStore('locale', () => {
  const locale = ref(i18n.global.locale.value)

  const elementLocale = computed(() => ELEMENT_LOCALE_MAP[locale.value] || zhCn)

  const localeOptions = computed(() =>
    LOCALE_OPTIONS.map((item) => ({
      value: item.value,
      label: i18n.global.t(item.labelKey),
    })),
  )

  function setLocale(nextLocale) {
    if (!ELEMENT_LOCALE_MAP[nextLocale]) {
      return
    }
    locale.value = nextLocale
    i18n.global.locale.value = nextLocale
    localStorage.setItem(LOCALE_STORAGE_KEY, nextLocale)
    applyDocumentLang(nextLocale)
    applyDocumentTitle()
  }

  function initLocale() {
    applyDocumentLang(locale.value)
    applyDocumentTitle()
  }

  return {
    locale,
    elementLocale,
    localeOptions,
    setLocale,
    initLocale,
  }
})
