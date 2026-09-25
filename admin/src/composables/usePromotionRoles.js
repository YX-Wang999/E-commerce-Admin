import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

function useRoleCodes() {
  const authStore = useAuthStore()
  const roleCodes = computed(() => authStore.user?.roles?.map((item) => item.code) || [])
  const isSuper = computed(() => Boolean(authStore.user?.is_superuser))
  return { roleCodes, isSuper }
}

/** Role-based permission helpers for promotion pages. */
export function usePromotionRoles() {
  const { roleCodes, isSuper } = useRoleCodes()

  const canCreateActivity = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => ['ops_manager', 'ops_staff', 'ops_director'].includes(code))
  })
  const canSubmitActivity = computed(() => isSuper.value || roleCodes.value.includes('ops_manager'))
  const canApproveActivity = computed(() => isSuper.value || roleCodes.value.includes('ops_director'))
  const canCancelActivity = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => ['ops_manager', 'ops_director'].includes(code))
  })
  const canEditActivity = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => ['ops_manager', 'ops_staff', 'ops_director'].includes(code))
  })
  const canDeleteActivity = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => ['ops_manager', 'ops_director'].includes(code))
  })

  const canCreateCoupon = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => ['ops_manager', 'ops_staff', 'ops_director'].includes(code))
  })
  const canEditCoupon = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => ['ops_manager', 'ops_staff', 'ops_director'].includes(code))
  })
  const canPublishCoupon = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => ['ops_manager', 'ops_director'].includes(code))
  })
  const canDeleteCoupon = computed(() => {
    if (isSuper.value) return true
    return roleCodes.value.some((code) => ['ops_manager', 'ops_director'].includes(code))
  })

  return {
    canCreateActivity,
    canSubmitActivity,
    canApproveActivity,
    canCancelActivity,
    canEditActivity,
    canDeleteActivity,
    canCreateCoupon,
    canEditCoupon,
    canPublishCoupon,
    canDeleteCoupon,
  }
}
