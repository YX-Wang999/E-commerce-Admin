const MONEY_CARD_KEYS = new Set(['today_income', 'total_revenue'])

export function formatMoney(value, { prefix = '¥' } = {}) {
  const amount = Number(value)
  if (Number.isNaN(amount)) return `${prefix}0.00`
  return `${prefix}${amount.toFixed(2)}`
}

export function formatDashboardCardValue(card) {
  if (!card) return ''
  if (MONEY_CARD_KEYS.has(card.key)) {
    return formatMoney(card.value, { prefix: '¥ ' })
  }
  return card.value
}
