import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

/** Role helpers for tenant management pages. */
export function useTenantRoles() {
  const authStore = useAuthStore()
  const roleCodes = computed(() => authStore.user?.roles?.map((item) => item.code) || [])
  const isSuper = computed(() => Boolean(authStore.user?.is_superuser))

  const canView = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => ['super_admin', 'ops_director', 'ops_manager'].includes(code))
  })

  const canCreate = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.includes('ops_director')
  })

  const canApprove = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.includes('ops_director')
  })

  const canSuspend = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.includes('ops_director')
  })

  const canDelete = computed(() => isSuper.value)

  const canViewChanges = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => ['ops_director', 'ops_manager'].includes(code))
  })

  const canReviewChanges = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.includes('ops_director')
  })

  return {
    canView,
    canCreate,
    canApprove,
    canSuspend,
    canDelete,
    canViewChanges,
    canReviewChanges,
  }
}
