/**
 * Validate route i18n registry against locale files and router meta.
 * Run: npm run check:i18n
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { ROUTE_I18N_KEYS } from '../src/router/i18nRegistry.js'
import zhCN from '../src/i18n/locales/zh-CN.js'
import enUS from '../src/i18n/locales/en-US.js'
import jaJP from '../src/i18n/locales/ja-JP.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const routerPath = path.resolve(__dirname, '../src/router/index.js')
const routerSource = readFileSync(routerPath, 'utf8')

const LOCALES = [
  { code: 'zh-CN', messages: zhCN },
  { code: 'en-US', messages: enUS },
  { code: 'ja-JP', messages: jaJP },
]

function hasNestedKey(obj, keyPath) {
  return keyPath.split('.').reduce((current, part) => current?.[part], obj) !== undefined
}

function extractRouterI18nKeys(source) {
  const entries = []
  let currentPath = null
  for (const line of source.split('\n')) {
    const pathMatch = line.match(/^\s*path:\s*'([^']+)'/)
    if (pathMatch) {
      currentPath = pathMatch[1]
    }
    const i18nMatch = line.match(/i18nKey:\s*'([^']+)'/)
    if (i18nMatch && currentPath) {
      entries.push({ path: currentPath, i18nKey: i18nMatch[1] })
      currentPath = null
    }
  }
  return entries
}

function toAbsolutePath(relativePath) {
  if (relativePath.startsWith('/')) {
    return relativePath
  }
  return `/${relativePath}`
}

const errors = []

for (const [routePath, i18nKey] of Object.entries(ROUTE_I18N_KEYS)) {
  for (const { code, messages } of LOCALES) {
    if (!hasNestedKey(messages, i18nKey)) {
      errors.push(`[${code}] missing i18n key "${i18nKey}" for route ${routePath}`)
    }
  }
}

const routerEntries = extractRouterI18nKeys(routerSource)
for (const { path: relativePath, i18nKey } of routerEntries) {
  const absolutePath = toAbsolutePath(relativePath)
  const registryKey = ROUTE_I18N_KEYS[absolutePath]
  if (!registryKey) {
    errors.push(`router has i18nKey "${i18nKey}" for ${absolutePath} but path is missing in i18nRegistry.js`)
    continue
  }
  if (registryKey !== i18nKey) {
    errors.push(
      `router meta.i18nKey "${i18nKey}" !== i18nRegistry "${registryKey}" for ${absolutePath}`,
    )
  }
}

for (const routePath of Object.keys(ROUTE_I18N_KEYS)) {
  const isDirectoryOnly = ['/products', '/orders', '/customers', '/reports', '/system', '/promotions'].includes(routePath)
  if (isDirectoryOnly) {
    continue
  }
  const hasRouterEntry = routerEntries.some(
    (entry) => toAbsolutePath(entry.path) === routePath,
  )
  if (!hasRouterEntry) {
    errors.push(`i18nRegistry has ${routePath} but router has no matching route with meta.i18nKey`)
  }
}

if (errors.length) {
  console.error('i18n route check failed:\n')
  errors.forEach((msg) => console.error(`  - ${msg}`))
  process.exit(1)
}

console.log(`i18n route check passed (${Object.keys(ROUTE_I18N_KEYS).length} paths, ${LOCALES.length} locales)`)
