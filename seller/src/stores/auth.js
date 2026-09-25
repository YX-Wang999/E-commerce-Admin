import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProfile, login as loginApi } from '@/api/auth'
import {
  clearAuthStorage,
  isLoggedIn,
  setTenantCode,
  setTenantInfo,
  setTokens,
} from '@/utils/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const tenant = ref(null)
  const staffRole = ref('')
  const menus = ref([])
  const loading = ref(false)

  async function login(form) {
    loading.value = true
    try {
      const res = await loginApi(form)
      setTokens(res.data.access, res.data.refresh)
      setTenantCode(res.data.tenant?.code)
      setTenantInfo(res.data.tenant)
      user.value = res.data.user
      tenant.value = res.data.tenant
      staffRole.value = res.data.staff_role || ''
      menus.value = res.data.menus || []
      return res
    } finally {
      loading.value = false
    }
  }

  async function fetchProfile() {
    if (!isLoggedIn()) {
      return null
    }
    const res = await getProfile()
    user.value = res.data.user
    tenant.value = res.data.tenant
    staffRole.value = res.data.staff_role || ''
    menus.value = res.data.menus || []
    if (res.data.tenant?.code) {
      setTenantCode(res.data.tenant.code)
      setTenantInfo(res.data.tenant)
    }
    return res.data
  }

  function logout() {
    user.value = null
    tenant.value = null
    staffRole.value = ''
    menus.value = []
    clearAuthStorage()
  }

  const isManager = () => ['owner', 'manager'].includes(staffRole.value)

  return {
    user,
    tenant,
    staffRole,
    menus,
    loading,
    login,
    fetchProfile,
    logout,
    isManager,
  }
})
