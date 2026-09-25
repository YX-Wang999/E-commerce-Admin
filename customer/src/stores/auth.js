import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getProfile } from '@/api/auth'
import {
  clearTokens,
  getAccessToken,
  isLoggedIn,
  setTokens,
} from '@/utils/auth'

export const useAuthStore = defineStore('auth', () => {
  const customer = ref(null)
  const token = ref(getAccessToken())
  const isLoggedInState = ref(isLoggedIn())

  async function login(credentials) {
    const res = await loginApi(credentials)
    token.value = res.data.access
    setTokens(res.data.access, res.data.refresh)
    isLoggedInState.value = true
    customer.value = res.data.customer

    let mergedGuestCount = 0
    try {
      const { useCartStore } = await import('@/stores/cart')
      mergedGuestCount = await useCartStore().mergeGuestCartToServer()
    } catch {
      mergedGuestCount = 0
    }

    return { ...res, mergedGuestCount }
  }

  async function fetchProfile() {
    if (!isLoggedIn()) {
      isLoggedInState.value = false
      customer.value = null
      return null
    }
    try {
      const res = await getProfile()
      customer.value = res.data
      token.value = getAccessToken()
      isLoggedInState.value = true
      return res.data
    } catch {
      if (!isLoggedIn()) {
        customer.value = null
        token.value = ''
        isLoggedInState.value = false
      }
      return null
    }
  }

  async function hydrateSession() {
    if (!isLoggedIn()) {
      isLoggedInState.value = false
      customer.value = null
      return null
    }
    isLoggedInState.value = true
    if (customer.value) {
      return customer.value
    }
    return fetchProfile()
  }

  function logout() {
    token.value = ''
    customer.value = null
    isLoggedInState.value = false
    clearTokens()
  }

  return {
    customer,
    token,
    isLoggedIn: isLoggedInState,
    login,
    fetchProfile,
    hydrateSession,
    logout,
  }
})
