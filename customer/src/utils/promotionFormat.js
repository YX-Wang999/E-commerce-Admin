import { formatPrice } from '@/utils/product'

export function formatCouponValue(coupon) {
  if (!coupon) return ''
  if (coupon.coupon_type === 'discount' && coupon.discount_rate) {
    const rate = Number(coupon.discount_rate)
    if (!Number.isNaN(rate)) {
      return `${(rate * 10).toFixed(1).replace(/\.0$/, '')}折`
    }
  }
  if (coupon.discount_amount) {
    return formatPrice(coupon.discount_amount)
  }
  return formatPrice(0)
}

export function formatCouponThreshold(coupon, t) {
  const min = Number(coupon?.min_amount || 0)
  if (min <= 0) {
    return t('coupon.noThreshold')
  }
  return t('coupon.threshold', { amount: formatPrice(min) })
}

export function formatCouponValidity(coupon, t) {
  if (coupon?.valid_type === 'after_receive') {
    return t('coupon.validAfterReceive', { days: coupon.valid_days || 7 })
  }
  if (coupon?.valid_start && coupon?.valid_end) {
    return `${coupon.valid_start.slice(0, 10)} ~ ${coupon.valid_end.slice(0, 10)}`
  }
  return t('coupon.validFlexible')
}

export function formatSeckillPhase(phase, t) {
  const map = {
    ongoing: t('seckill.statusOngoing'),
    upcoming: t('seckill.statusUpcoming'),
    ended: t('seckill.statusEnded'),
  }
  return map[phase] || phase
}
