const STYLE_ID = 'app-dialog-style-fix'

const CSS = `
html, body {
  color-scheme: light !important;
}

body .van-dialog,
body .van-dialog.app-confirm-dialog {
  --van-text-color: #323233 !important;
  --van-text-color-2: #646566 !important;
  --van-dialog-background: #ffffff !important;
  --van-dialog-has-title-message-text-color: #646566 !important;
  --van-dialog-confirm-button-text-color: #ee0a24 !important;
  background: #ffffff !important;
  color: #323233 !important;
}

body .van-dialog .van-dialog__header,
body .van-dialog .van-dialog__title {
  color: #323233 !important;
}

body .van-dialog .van-dialog__message,
body .van-dialog .van-dialog__content,
body .van-dialog .van-dialog__message--has-title {
  color: #646566 !important;
}

body .van-dialog .van-dialog__footer .van-dialog__cancel,
body .van-dialog .van-dialog__footer .van-dialog__cancel .van-button__text {
  color: #646566 !important;
}

body .van-dialog .van-dialog__footer .van-dialog__confirm,
body .van-dialog .van-dialog__footer .van-dialog__confirm .van-button__text {
  color: #ee0a24 !important;
}

body .app-confirm-dialog__title {
  color: #323233 !important;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 12px;
}

body .app-confirm-dialog__message {
  color: #646566 !important;
  font-size: 14px;
  line-height: 1.6;
  text-align: center;
}
`.trim()

export function injectDialogStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLE_ID)) return

  const style = document.createElement('style')
  style.id = STYLE_ID
  style.textContent = CSS
  document.head.appendChild(style)
}
