/** Resolve E.164 phone from vue-tel-num-input model or raw string. */

import { parsePhoneNumberFromString } from 'libphonenumber-js'

export function telModelToE164(val) {
  if (!val?.value?.trim()) return ''
  const raw = String(val.value).trim()
  if (raw.startsWith('+')) {
    const parsed = parsePhoneNumberFromString(raw)
    return parsed?.isValid() ? parsed.number : raw.replace(/\s/g, '')
  }
  if (val.iso) {
    const parsed = parsePhoneNumberFromString(raw, val.iso)
    if (parsed?.isValid()) return parsed.number
  }
  const digits = raw.replace(/\D/g, '')
  const dial = (val.code || '').replace(/\D/g, '')
  return digits && dial ? `+${dial}${digits}` : ''
}

export function toE164Phone(value, defaultCountry = 'CN') {
  const raw = (value || '').trim().replace(/\s/g, '')
  if (!raw) return ''
  if (raw.startsWith('+')) {
    const parsed = parsePhoneNumberFromString(raw)
    return parsed?.isValid() ? parsed.number : raw
  }
  const parsed = parsePhoneNumberFromString(raw, defaultCountry)
  return parsed?.isValid() ? parsed.number : ''
}

export function isValidE164Phone(value) {
  const phone = (value || '').trim()
  if (!phone.startsWith('+')) return false
  const parsed = parsePhoneNumberFromString(phone)
  return Boolean(parsed?.isValid())
}
