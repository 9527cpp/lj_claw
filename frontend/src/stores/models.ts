import { defineStore } from 'pinia'
import { ref } from 'vue'
import { modelsApi } from '@/api'

export interface ModelConfig {
  id: string
  name: string
  provider: string
  api_key: string
  api_base: string
  enabled: boolean
}

export const useModelsStore = defineStore('models', () => {
  const models = ref<ModelConfig[]>([])
  const activeModel = ref<string | null>(null)
  const loading = ref(false)

  async function fetchModels() {
    loading.value = true
    try {
      const res = await modelsApi.list()
      models.value = res.data.models || []
      activeModel.value = res.data.active_model
    } finally {
      loading.value = false
    }
  }

  async function addModel(model: Omit<ModelConfig, 'enabled'>) {
    const res = await modelsApi.create({ ...model, enabled: true })
    await fetchModels()
    return res
  }

  async function updateModel(id: string, model: ModelConfig) {
    await modelsApi.update(id, model)
    await fetchModels()
  }

  async function deleteModel(id: string) {
    await modelsApi.delete(id)
    await fetchModels()
  }

  async function setActive(id: string) {
    await modelsApi.setActive(id)
    activeModel.value = id
  }

  return { models, activeModel, loading, fetchModels, addModel, updateModel, deleteModel, setActive }
})