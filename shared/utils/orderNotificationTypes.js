/** Notification types that should refresh order badges / alerts. */
export const ORDER_RELATED_NOTIFICATION_TYPES = new Set([
  'order',
  'order_new',
  'order_paid',
  'order_shipped',
  'order_completed',
  'order_cancelled',
  'refund',
  'refund_applied',
  'refund_reviewed',
])

export function isOrderRelatedNotification(type) {
  return ORDER_RELATED_NOTIFICATION_TYPES.has(type)
}
