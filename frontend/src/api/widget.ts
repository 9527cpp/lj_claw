import axios from 'axios'

export const widgetApi = {
  listSites() {
    return axios.get('/api/widget/sites')
  },

  createSite(data: any) {
    return axios.post('/api/widget/sites', data)
  },

  updateSite(siteId: string, data: any) {
    return axios.put(`/api/widget/sites/${siteId}`, data)
  },

  deleteSite(siteId: string) {
    return axios.delete(`/api/widget/sites/${siteId}`)
  },

  regenerateKey(siteId: string) {
    return axios.post(`/api/widget/sites/${siteId}/regenerate-key`)
  }
}