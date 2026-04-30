import { defineStore } from 'pinia'
import { ref } from 'vue'
import { skillsApi } from '@/api'

export interface Skill {
  id: string
  name: string
  enabled: boolean
  config: Record<string, any>
}

export interface ImportSource {
  source: string
  path: string
  type: string
  skills: { id: string; name: string }[]
}

export const useSkillsStore = defineStore('skills', () => {
  const skills = ref<Skill[]>([])
  const importSources = ref<ImportSource[]>([])
  const loading = ref(false)

  async function fetchSkills() {
    loading.value = true
    try {
      const res = await skillsApi.list()
      skills.value = res.data.skills || []
    } finally {
      loading.value = false
    }
  }

  async function fetchImportSources() {
    const res = await skillsApi.listSources()
    importSources.value = res.data.sources || []
  }

  async function toggleSkill(id: string, enabled: boolean) {
    await skillsApi.toggle(id, enabled)
    const skill = skills.value.find(s => s.id === id)
    if (skill) skill.enabled = enabled
  }

  async function updateSkill(id: string, config: Record<string, any>) {
    const skill = skills.value.find(s => s.id === id)
    if (!skill) return
    await skillsApi.update(id, { ...skill, config })
    skill.config = config
  }

  async function importSkill(source: string) {
    const res = await skillsApi.import(source)
    await fetchSkills()
    await fetchImportSources()
    return res.data
  }

  async function unimportSkill(source: string) {
    const res = await skillsApi.unimport(source)
    await fetchSkills()
    await fetchImportSources()
    return res.data
  }

  return { skills, importSources, loading, fetchSkills, fetchImportSources, toggleSkill, updateSkill, importSkill, unimportSkill }
})