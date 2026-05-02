<template>
  <div class="skill-toggle">
    <div class="skill-info">
      <span class="skill-name">{{ skill.name }}</span>
      <div v-if="skill.id === 'weather'" class="skill-config">
        <div class="config-row">
          <label class="config-label">API Host</label>
          <input
            v-model="apiHost"
            type="text"
            placeholder="devapi.qweather.com"
            class="config-input"
            @blur="saveConfig"
          />
        </div>
        <div class="config-row">
          <label class="config-label">API Key</label>
          <input
            v-model="apiKey"
            type="password"
            placeholder="和风天气 API Key"
            class="config-input"
            @blur="saveConfig"
          />
        </div>
      </div>
    </div>
    <label class="switch">
      <input type="checkbox" :checked="skill.enabled" @change="handleToggle" />
      <span class="slider"></span>
    </label>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Skill } from '@/stores/skills'
import { useSkillsStore } from '@/stores/skills'

const props = defineProps<{ skill: Skill }>()
const emit = defineEmits<{ toggle: [id: string, enabled: boolean] }>()

const skillsStore = useSkillsStore()
const apiHost = ref(props.skill.config?.api_host || 'devapi.qweather.com')
const apiKey = ref(props.skill.config?.api_key || '')

watch(() => props.skill.config, (newConfig) => {
  apiHost.value = newConfig?.api_host || 'devapi.qweather.com'
  apiKey.value = newConfig?.api_key || ''
}, { deep: true })

function handleToggle(e: Event) {
  const target = e.target as HTMLInputElement
  emit('toggle', props.skill.id, target.checked)
}

async function saveConfig() {
  const newConfig = {
    ...props.skill.config,
    api_host: apiHost.value,
    api_key: apiKey.value
  }
  if (JSON.stringify(newConfig) !== JSON.stringify(props.skill.config)) {
    await skillsStore.updateSkill(props.skill.id, newConfig)
  }
}
</script>

<style scoped>
.skill-toggle {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 14px 18px;
  background: white;
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid #e6dfd8;
  transition: border-color 0.2s;
}
.skill-toggle:hover {
  border-color: #d8d0c4;
}
.skill-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.skill-name {
  font-size: 14px;
  font-weight: 500;
  color: #141413;
}
.skill-config {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.config-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.config-label {
  font-size: 12px;
  color: #6c6a64;
  min-width: 52px;
}
.config-input {
  padding: 8px 12px;
  border: 1px solid #e6dfd8;
  border-radius: 5px;
  font-size: 13px;
  width: 240px;
  background: #faf9f5;
  color: #141413;
}
.config-input:focus {
  outline: none;
  border-color: #cc785c;
}
.config-input::placeholder {
  color: #8e8b82;
}

/* Toggle Switch */
.switch {
  position: relative;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: #d8d0c4;
  border-radius: 24px;
  transition: 0.3s;
}
.slider::before {
  content: "";
  position: absolute;
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: 0.3s;
}
input:checked + .slider {
  background: #5db8a6;
}
input:checked + .slider::before {
  transform: translateX(20px);
}
</style>