/**
 * Map backend notification related_url to customer SPA routes.
 * @param {string | null | undefined} relatedUrl
 * @returns {import('vue-router').RouteLocationRaw | null}
 */
export function resolveNotificationRoute(relatedUrl) {
  if (!relatedUrl) return null

  const raw = String(relatedUrl).trim()
  if (!raw) return null

  const [pathPart, queryPart] = raw.split('?')
  const path = pathPart.replace(/\/+$/, '') || '/'
  const query = queryPart ? Object.fromEntries(new URLSearchParams(queryPart)) : undefined

  const orderDetailMatch = path.match(/^\/orders\/(\d+)$/)
  if (orderDetailMatch) {
    return { name: 'OrderDetail', params: { id: orderDetailMatch[1] }, query }
  }

  if (path === '/orders') {
    return { name: 'OrderList', query }
  }

  if (path === '/order' && query?.id) {
    return { name: 'OrderDetail', params: { id: String(query.id) } }
  }

  return query ? { path, query } : path
}
