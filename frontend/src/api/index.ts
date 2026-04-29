import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

export const modelsApi = {
  list: () => api.get('/models/'),
  create: (data: any) => api.post('/models/', data),
  update: (id: string, data: any) => api.put(`/models/${id}/`, data),
  delete: (id: string) => api.delete(`/models/${id}/`),
  setActive: (id: string) => api.put(`/models/${id}/active`)
}

export const skillsApi = {
  list: () => api.get('/skills/'),
  update: (id: string, data: any) => api.put(`/skills/${id}`, data),
  toggle: (id: string, enabled: boolean) => api.put(`/skills/${id}/enabled?enabled=${enabled}`)
}

export const chatApi = {
  send: (message: string, modelId?: string) => {
    return api.post('/chat/', { message, model_id: modelId }, {
      responseType: 'stream'
    })
  },
  history: () => api.get('/chat/history'),
  clearHistory: () => api.delete('/chat/history')
}

export default api