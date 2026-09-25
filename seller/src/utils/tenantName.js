/** Client-side tenant name validation (mirrors backend rules). */

const TENANT_NAME_PATTERN = /^[\u4e00-\u9fa5a-zA-Z0-9·\- ]{2,50}$/

export function nameEffectiveLength(name) {
  let total = 0
  for (const char of name) {
    if (/[\u4e00-\u9fa5]/.test(char)) total += 2
    else total += 1
  }
  return total
}

export function isAllDigitsOrSymbols(name) {
  const stripped = name.replace(/[\s·\-]/g, '')
  if (!stripped) return true
  if (/^\d+$/.test(stripped)) return true
  return !/[\u4e00-\u9fa5a-zA-Z]/.test(stripped)
}

export function validateTenantName(name) {
  const value = (name || '').trim()
  if (!value) return '商户名称不能为空'
  if (!TENANT_NAME_PATTERN.test(value)) {
    return '名称仅允许中文、英文、数字、点、横杠和空格，长度 2-50 个字符'
  }
  if (nameEffectiveLength(value) < 4) {
    return '名称长度至少 2 个汉字或 4 个字符'
  }
  if (isAllDigitsOrSymbols(value)) {
    return '商户名称不能全是数字或特殊符号'
  }
  return ''
}

export const TENANT_NAME_HINT = '请使用有辨识度的名称，如「北京张三科技」，便于客户识别和搜索'
