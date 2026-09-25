/** Menu label resolution: route meta > menu.{path_key} > menuByPath (legacy) > fallback. */

import { ROUTE_I18N_KEYS } from '@/router/i18nRegistry'

/**
 * Convert route path to flat menu key.
 * /products/list -> products_list
 * /profile/change-password -> profile_change_password
 */
export function pathToMenuKey(path) {
  if (!path) {
    return ''
  }
  return path.replace(/^\//, '').replace(/\//g, '_').replace(/-/g, '_')
}

/** Human-readable fallback from path last segment. */
export function formatPathFallback(path) {
  const last = path.split('/').filter(Boolean).pop() || 'home'
  return last
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

/**
 * Resolve sidebar / menu label for a path.
 * @param {Function} t - vue-i18n translate
 * @param {Function} te - vue-i18n exists check
 * @param {string} path - menu path e.g. /products/list
 * @param {string} fallbackTitle - backend Chinese title
 */
export function resolveMenuLabel(t, te, path, fallbackTitle = '') {
  if (!path) {
    return fallbackTitle
  }

  const routeKey = ROUTE_I18N_KEYS[path]
  if (routeKey && te(routeKey)) {
    return t(routeKey)
  }

  const menuKey = `menu.${pathToMenuKey(path)}`
  if (te(menuKey)) {
    return t(menuKey)
  }

  const legacyKey = `menuByPath.${path}`
  if (te(legacyKey)) {
    return t(legacyKey)
  }

  const formatted = formatPathFallback(path)
  if (formatted) {
    return formatted
  }

  return fallbackTitle
}
