import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getTenant,
  getTenantSummary,
  getTenants,
} from '@/api/tenant'

const TENANT_LIST_PATH = '/tenants/list'

export const useTenantStore = defineStore('tenant', () => {
  const tenants = ref([])
  const currentTenant = ref(null)
  const stats = ref({ total: 0, pending: 0, active: 0, suspended: 0, closed: 0 })
  let statsPollTimer = null

  async function fetchList(params) {
    const res = await getTenants(params)
    tenants.value = res.data.results || res.data || []
    return res.data
  }

  async function fetchStats() {
    const res = await getTenantSummary()
    stats.value = res.data || stats.value
    return res.data
  }

  function startStatsPolling(intervalMs = 60000) {
    stopStatsPolling()
    fetchStats()
    statsPollTimer = window.setInterval(fetchStats, intervalMs)
  }

  function stopStatsPolling() {
    if (statsPollTimer) {
      clearInterval(statsPollTimer)
      statsPollTimer = null
    }
  }

  function getBadgeForPath(path) {
    if (path === TENANT_LIST_PATH && stats.value.pending > 0) {
      return stats.value.pending > 99 ? '99+' : stats.value.pending
    }
    return ''
  }

  async function fetchDetail(id) {
    const res = await getTenant(id)
    currentTenant.value = res.data
    return res.data
  }

  function clearCurrent() {
    currentTenant.value = null
  }

  return {
    tenants,
    currentTenant,
    stats,
    fetchList,
    fetchStats,
    fetchDetail,
    clearCurrent,
    startStatsPolling,
    stopStatsPolling,
    getBadgeForPath,
  }
})
