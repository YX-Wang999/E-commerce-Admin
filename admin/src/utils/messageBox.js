import { h } from 'vue'
import { ElMessageBox } from 'element-plus'

const DIALOG_CLASS = 'app-confirm-dialog'

export function confirmDialog(message, title, options = {}) {
  const content =
    typeof message === 'string'
      ? h(
          'p',
          {
            style: {
              color: '#606266',
              margin: '0',
              lineHeight: '1.6',
              fontSize: '14px',
            },
          },
          message,
        )
      : message

  return ElMessageBox.confirm(content, title, {
    customClass: DIALOG_CLASS,
    confirmButtonText: options.confirmButtonText,
    cancelButtonText: options.cancelButtonText,
    type: options.type,
    ...options,
  })
}
