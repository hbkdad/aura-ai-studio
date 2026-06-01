import axios from 'axios'

const BASE = '/api'

export const api = axios.create({ baseURL: BASE })

// Intercept responses — convert pydantic validation errors into readable messages
api.interceptors.response.use(
  res => res,
  err => {
    const detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      // Pydantic v2 returns an array of error objects
      const messages = detail.map(e => {
        const field = e.loc?.slice(1).join('.') || 'field'
        return `${field}: ${e.msg}`
      })
      err.friendlyMessage = messages.join(' | ')
    } else if (typeof detail === 'string') {
      err.friendlyMessage = detail
    } else {
      err.friendlyMessage = 'An unexpected error occurred. Please try again.'
    }
    return Promise.reject(err)
  }
)

export const health = () => api.get('/health')

export const postManualRevenue = (data) => api.post('/revenue/manual', data)
export const getRevenue = (limit = 100, offset = 0) =>
  api.get(`/revenue?limit=${limit}&offset=${offset}`)

export const getTreasurySummary = () => api.get('/treasury/summary')
export const postTreasuryCalculate = (data) => api.post('/treasury/calculate', data)
// PUT body — percentages must sum to 100
export const putTreasuryRules = (body) => api.put('/treasury/rules', body)

export const getBtcAllocations = () => api.get('/btc/allocations')

export const postWebsiteAudit = (data) => api.post('/agents/website-audit', data)
export const getAgentActions = (limit = 50) => api.get(`/agents/actions?limit=${limit}`)

export const postPaperAllocation = (data) => api.post('/wallet/paper/simulate-allocation', data)

export const getRevenueCSV = () => api.get('/exports/revenue-csv', { responseType: 'blob' })

export const postKillSwitch = (active, reason = '') =>
  api.post('/safety/kill-switch', { active, reason })
export const getSafetySettings = () => api.get('/safety/settings')
// PUT body — no longer query params
export const putSafetySettings = (body) => api.put('/safety/settings', body)

export const postFakeSale = () => api.post('/test/fake-sale')
