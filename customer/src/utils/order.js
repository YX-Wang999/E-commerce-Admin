export function isOrderExpired(order) {
  const expiresAt = order?.expires_at
  if (!expiresAt) return false
  const date = new Date(expiresAt)
  if (Number.isNaN(date.getTime())) return false
  return date.getTime() <= Date.now()
}

/** Pending payment orders can be cancelled directly without merchant review. */
export function canDirectCancelOrder(order) {
  return order?.status === 'pending' && !isOrderExpired(order)
}
