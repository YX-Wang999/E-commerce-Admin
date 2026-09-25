import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const MANAGE_ROLES = ['ops_director', 'ops_manager']

export function useCategoryRoles() {
  const authStore = useAuthStore()
  const roleCodes = computed(() => authStore.user?.roles?.map((item) => item.code) || [])
  const isSuper = computed(() => Boolean(authStore.user?.is_superuser))

  const canManageCategory = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => MANAGE_ROLES.includes(code))
  })

  return { canManageCategory }
}
