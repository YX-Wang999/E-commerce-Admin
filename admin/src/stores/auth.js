import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProfile, login as loginApi } from '@/api/auth'
import { clearTokens, isLoggedIn, setTokens } from '@/utils/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const menus = ref([])
  const loading = ref(false)

  async function login(form) {
    loading.value = true
    try {
      const res = await loginApi(form)
      setTokens(res.data.access, res.data.refresh)
      user.value = res.data.user
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
    menus.value = res.data.menus || []
    return res.data
  }

  function logout() {
    user.value = null
    menus.value = []
    clearTokens()
  }

  return {
    user,
    menus,
    loading,
    login,
    fetchProfile,
    logout,
  }
})
