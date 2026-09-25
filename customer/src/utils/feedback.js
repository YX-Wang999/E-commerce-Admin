import { showFailToast, showSuccessToast, showToast } from 'vant'
import i18n from '@/i18n'

const { t } = i18n.global

export function resolveErrorMessage(error, fallbackKey = 'common.failed') {
  if (!error) return t(fallbackKey)
  if (typeof error === 'string') return error

  if (typeof error.message === 'string' && error.message) {
    if (/timeout/i.test(error.message)) return t('common.requestTimeout')
    return error.message
  }

  const code = error.code
  if (code && typeof code === 'number') {
    const codeKey = `auth.errorCodes.${code}`
    const translated = t(codeKey)
    if (translated !== codeKey) return translated
  }
  return t(fallbackKey)
}

export function toastSuccess(message) {
  showSuccessToast({
    message,
    className: 'app-toast app-toast--success',
  })
}

export function toastError(message) {
  const text = message || t('common.failed')
  showFailToast({
    message: text,
    className: 'app-toast app-toast--fail',
  })
}

export function toastInfo(message) {
  showToast({
    message,
    className: 'app-toast app-toast--info',
  })
}
