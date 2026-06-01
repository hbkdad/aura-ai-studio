import axios from 'axios'

const BASE = '/api'

export const api = axios.create({ baseURL: BASE })

export const health = () => api.get('/health')

export const postManualRevenue = (data) => api.post('/revenue/manual', data)
export const getRevenue = (limit = 100, offset = 0) => api.get(`/revenue?limit=${limit}&offset=${offset}`)

export const getTreasurySummary = () => api.get('/treasury/summary')
export const postTreasuryCalculate = (data) => api.post('/treasury/calculate', data)
export const putTreasuryRules = (params) => api.put('/treasury/rules', null, { params })

export const getBtcAllocations = () => api.get('/btc/allocations')

export const postWebsiteAudit = (data) => api.post('/agents/website-audit', data)
export const getAgentActions = (limit = 50) => api.get(`/agents/actions?limit=${limit}`)

export const postPaperAllocation = (data) => api.post('/wallet/paper/simulate-allocation', data)

export const getRevenueCSV = () => api.get('/exports/revenue-csv', { responseType: 'blob' })

export const postKillSwitch = (active, reason = '') => api.post('/safety/kill-switch', { active, reason })
export const getSafetySettings = () => api.get('/safety/settings')
export const putSafetySettings = (params) => api.put('/safety/settings', null, { params })
