/**
 * One-time migration script: split monolithic locale files into shared core + domain files.
 * Run: node scripts/split-i18n.mjs
 */
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const ROOT = path.resolve(import.meta.dirname, '..')
const SHARED_CORE = path.join(ROOT, 'shared/i18n/core')
const SHARED_BUSINESS = path.join(ROOT, 'shared/i18n/business')

const LOCALES = ['zh-CN', 'en-US', 'ja-JP']

const ORDER_STATUS_KEYS = [
  'statusPending',
  'statusPaid',
  'statusShipped',
  'statusCompleted',
  'statusCancelled',
  'statusRefunding',
  'orderNo',
  'paidAt',
]

const PRODUCT_SHARED_KEYS = ['name', 'price', 'stock', 'description', 'category', 'brand']

function pick(obj, keys) {
  const result = {}
  for (const key of keys) {
    if (obj?.[key] !== undefined) result[key] = obj[key]
  }
  return result
}

function serializeModule(obj, comment) {
  return `${comment}\n\nexport default ${JSON.stringify(obj, null, 2)}\n`
}

async function loadLocale(filePath) {
  const mod = await import(pathToFileURL(filePath))
  return mod.default
}

async function splitApp(appName, domainDir, domainFilePrefix, omitFromDomain = ['common', 'locale']) {
  const coreByLocale = {}
  const domainByLocale = {}
  const orderBiz = {}
  const productBiz = {}

  for (const locale of LOCALES) {
    const filePath = path.join(ROOT, appName, 'src/i18n/locales', `${locale}.js`)
    const messages = await loadLocale(filePath)
    coreByLocale[locale] = {
      common: messages.common,
      locale: messages.locale,
    }
    const domain = { ...messages }
    for (const key of omitFromDomain) delete domain[key]

    if (domain.order) {
      orderBiz[locale] = { order: pick(domain.order, ORDER_STATUS_KEYS) }
      for (const key of ORDER_STATUS_KEYS) {
        if (domain.order[key] !== undefined) delete domain.order[key]
      }
    }
    if (domain.product) {
      productBiz[locale] = { product: pick(domain.product, PRODUCT_SHARED_KEYS) }
      for (const key of PRODUCT_SHARED_KEYS) {
        if (domain.product[key] !== undefined) delete domain.product[key]
      }
    }
    if (domain.checkout) {
      const checkoutStatusKeys = [
        'statusPending',
        'statusPaid',
        'statusShipped',
        'statusCompleted',
        'statusCancelled',
        'paidAt',
        'orderNo',
      ]
      const picked = pick(domain.checkout, checkoutStatusKeys)
      if (Object.keys(picked).length) {
        orderBiz[locale] = orderBiz[locale] || { order: {} }
        Object.assign(orderBiz[locale].order, picked)
      }
    }

    domainByLocale[locale] = domain
  }

  fs.mkdirSync(domainDir, { recursive: true })
  for (const locale of LOCALES) {
    fs.writeFileSync(
      path.join(domainDir, `${domainFilePrefix}.${locale}.js`),
      serializeModule(domainByLocale[locale], `/** ${appName} domain — ${locale} */`),
    )
  }

  return { coreByLocale, orderBiz, productBiz }
}

function writeCore(coreByLocale) {
  fs.mkdirSync(SHARED_CORE, { recursive: true })
  for (const locale of LOCALES) {
    fs.writeFileSync(
      path.join(SHARED_CORE, `${locale}.js`),
      serializeModule(coreByLocale[locale], `/** Shared core — ${locale} */`),
    )
  }
}

function mergeOrderBiz(...parts) {
  const result = {}
  for (const locale of LOCALES) {
    result[locale] = { order: {} }
    for (const part of parts) {
      if (part[locale]?.order) Object.assign(result[locale].order, part[locale].order)
    }
  }
  return result
}

function mergeProductBiz(...parts) {
  const result = {}
  for (const locale of LOCALES) {
    result[locale] = { product: {} }
    for (const part of parts) {
      if (part[locale]?.product) Object.assign(result[locale].product, part[locale].product)
    }
  }
  return result
}

const admin = await splitApp('admin', path.join(ROOT, 'admin/src/i18n/domains'), 'admin')
const customer = await splitApp('customer', path.join(ROOT, 'customer/src/i18n/domains'), 'customer')

const coreByLocale = {}
for (const locale of LOCALES) {
  coreByLocale[locale] = {
    common: { ...customer.coreByLocale[locale].common, ...admin.coreByLocale[locale].common },
    locale: admin.coreByLocale[locale].locale,
  }
}
writeCore(coreByLocale)

const orderBusiness = mergeOrderBiz(admin.orderBiz, customer.orderBiz)
const productBusiness = mergeProductBiz(admin.productBiz, customer.productBiz)

fs.mkdirSync(SHARED_BUSINESS, { recursive: true })
fs.writeFileSync(
  path.join(SHARED_BUSINESS, 'order.js'),
  serializeModule(orderBusiness, '/** Shared order business domain (all locales) */'),
)
fs.writeFileSync(
  path.join(SHARED_BUSINESS, 'product.js'),
  serializeModule(productBusiness, '/** Shared product business domain (all locales) */'),
)

const authBusiness = {}
for (const locale of LOCALES) {
  const customerDomain = await loadLocale(
    path.join(ROOT, 'customer/src/i18n/domains', `customer.${locale}.js`),
  )
  const customerAuth = customerDomain.auth || {}
  authBusiness[locale] = {
    auth: pick(customerAuth, [
      'password',
      'passwordRequired',
      'passwordPlaceholder',
      'login',
      'loginSuccess',
      'loginFailed',
      'logout',
      'accountRequired',
      'emailInvalid',
    ]),
  }
}
fs.writeFileSync(
  path.join(SHARED_BUSINESS, 'auth.js'),
  serializeModule(authBusiness, '/** Shared auth business domain (all locales) */'),
)

console.log('Split complete: shared/i18n + admin/customer domains')
