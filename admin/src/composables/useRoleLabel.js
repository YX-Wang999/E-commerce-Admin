import { useRoleDisplayStore } from '@/stores/roleDisplay'
import { useLocaleStore } from '@/stores/locale'

export function useRoleLabel() {
  const roleDisplayStore = useRoleDisplayStore()
  const localeStore = useLocaleStore()

  function currentLocale() {
    return localeStore.locale
  }

  function roleLabel(code, fallback = '') {
    return roleDisplayStore.getLabel(code, currentLocale(), fallback)
  }

  function roleLabels(roles) {
    return roleDisplayStore.formatRoles(roles, currentLocale())
  }

  function roleOptionLabel(role) {
    return roleDisplayStore.getLabel(role.code, currentLocale(), role.name)
  }

  return {
    roleLabel,
    roleLabels,
    roleOptionLabel,
  }
}
