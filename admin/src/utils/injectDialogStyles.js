const STYLE_ID = 'app-dialog-style-fix'

const CSS = `
html, body {
  color-scheme: light !important;
}

body .el-message-box,
body .el-message-box.app-confirm-dialog {
  --el-bg-color: #ffffff !important;
  --el-text-color-primary: #303133 !important;
  --el-text-color-regular: #606266 !important;
  --el-messagebox-title-color: #303133 !important;
  --el-messagebox-content-color: #606266 !important;
  background-color: #ffffff !important;
  color: #303133 !important;
}

body .el-message-box .el-message-box__header,
body .el-message-box .el-message-box__title {
  color: #303133 !important;
}

body .el-message-box .el-message-box__message,
body .el-message-box .el-message-box__message p,
body .el-message-box .el-message-box__content {
  color: #606266 !important;
}

body .el-message-box .el-message-box__btns .el-button--default {
  color: #606266 !important;
  --el-button-text-color: #606266 !important;
  background-color: #ffffff !important;
  border-color: #dcdfe6 !important;
}

body .el-message-box .el-message-box__btns .el-button--primary {
  color: #ffffff !important;
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
