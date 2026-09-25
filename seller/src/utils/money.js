export function formatMoney(value, { prefix = '¥' } = {}) {
  const amount = Number(value)
  if (Number.isNaN(amount)) return `${prefix}0.00`
  return `${prefix}${amount.toFixed(2)}`
}
