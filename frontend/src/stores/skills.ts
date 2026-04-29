import { defineStore } from 'pinia'
import { ref } from 'vue'
import { skillsApi } from '@/api'

export interface Skill {
  id: string
  name: string
  enabled: boolean
  config: Record<string, any>
}

export const useSkillsStore = defineStore('skills', () => {
  const skills = ref<Skill[]>([])
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

  return { skills, loading, fetchSkills, toggleSkill, updateSkill }
})