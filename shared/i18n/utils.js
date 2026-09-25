/**
 * Deep-merge locale message objects (later keys override earlier).
 * Arrays are replaced, not concatenated.
 */
export function deepMerge(...sources) {
  const result = {}
  for (const source of sources) {
    if (!source || typeof source !== 'object') continue
    mergeInto(result, source)
  }
  return result
}

function mergeInto(target, source) {
  for (const [key, value] of Object.entries(source)) {
    if (
      value
      && typeof value === 'object'
      && !Array.isArray(value)
      && target[key]
      && typeof target[key] === 'object'
      && !Array.isArray(target[key])
    ) {
      mergeInto(target[key], value)
    } else {
      target[key] = value
    }
  }
}

export function mergeMessages(...parts) {
  return deepMerge(...parts)
}

export function buildLocaleMessages(locale, modules) {
  return mergeMessages(...modules.map((module) => module[locale] || module.default?.[locale] || {}))
}

export const SUPPORTED_LOCALES = ['zh-CN', 'en-US', 'ja-JP']

export function buildAllLocaleMessages({ core, business = [], domain = {} }) {
  const messages = {}
  for (const locale of SUPPORTED_LOCALES) {
    messages[locale] = mergeMessages(
      core[locale] || {},
      ...business.map((item) => item[locale] || {}),
      domain[locale] || {},
    )
  }
  return messages
}
