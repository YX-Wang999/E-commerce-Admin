import { reactive } from 'vue'
import i18n from '@/i18n'

const state = reactive({
  show: false,
  title: '',
  message: '',
  cancelText: '',
  confirmText: '',
})

let pending = null

export function getConfirmState() {
  return state
}

export function resolveConfirm() {
  state.show = false
  pending?.resolve('confirm')
  pending = null
}

export function rejectConfirm() {
  state.show = false
  pending?.reject('cancel')
  pending = null
}

export function confirmDialog(options = {}) {
  const { t } = i18n.global

  return new Promise((resolve, reject) => {
    state.title = options.title ?? ''
    state.message = options.message ?? ''
    state.cancelText = options.cancelButtonText ?? t('common.cancel')
    state.confirmText = options.confirmButtonText ?? t('common.confirm')
    state.show = true
    pending = { resolve, reject }
  })
}
