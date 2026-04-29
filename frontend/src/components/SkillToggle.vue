<template>
  <div class="skill-toggle">
    <span class="skill-name">{{ skill.name }}</span>
    <label class="switch">
      <input type="checkbox" :checked="skill.enabled" @change="handleToggle" />
      <span class="slider"></span>
    </label>
  </div>
</template>

<script setup lang="ts">
import type { Skill } from '@/stores/skills'

const props = defineProps<{ skill: Skill }>()
const emit = defineEmits<{ toggle: [id: string, enabled: boolean] }>()

function handleToggle(e: Event) {
  const target = e.target as HTMLInputElement
  emit('toggle', props.skill.id, target.checked)
}
</script>

<style scoped>
.skill-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  margin-bottom: 8px;
}
.skill-name { font-weight: 500; }
.switch {
  position: relative;
  width: 48px;
  height: 24px;
}
.switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: #ccc;
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
input:checked + .slider { background: #4CAF50; }
input:checked + .slider::before { transform: translateX(24px); }
</style>