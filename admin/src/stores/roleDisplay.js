import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getPublicSettings, getRoleDisplayNames, updateRoleDisplayNames } from '@/api/system'

export const useRoleDisplayStore = defineStore('roleDisplay', () => {
  const merged = ref({})
  const loaded = ref(false)

  function applyMerged(data) {
    if (data && typeof data === 'object') {
      merged.value = data
      loaded.value = true
    }
  }

  async function fetchFromPublic() {
    try {
      const res = await getPublicSettings()
      const raw = res.data?.role_display_names
      if (raw && typeof raw === 'object') {
        applyMerged(raw)
      }
    } catch {
      // ignore — fall back to role.name from API
    }
  }

  async function fetchFull() {
    const res = await getRoleDisplayNames()
    applyMerged(res.data?.merged || {})
    return res.data
  }

  async function saveCustom(payload) {
    const res = await updateRoleDisplayNames(payload)
    applyMerged(res.data?.merged || {})
    return res
  }

  function getLabel(code, locale, fallback = '') {
    if (!code) return fallback || '-'
    const names = merged.value[code]
    if (names) {
      const custom = names[locale]
      if (custom) return custom
      if (names['zh-CN']) return names['zh-CN']
    }
    return fallback || code
  }

  function formatRoles(roles, locale) {
    if (!roles?.length) return '-'
    return roles.map((role) => getLabel(role.code, locale, role.name)).join('、')
  }

  return {
    merged,
    loaded,
    fetchFromPublic,
    fetchFull,
    saveCustom,
    getLabel,
    formatRoles,
  }
})
