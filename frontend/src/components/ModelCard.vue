<template>
  <div class="model-card" :class="{ active: isActive }">
    <div class="model-header">
      <h3>{{ model.name }}</h3>
      <span class="provider">{{ model.provider }}</span>
    </div>
    <div class="model-body">
      <p><strong>API Base:</strong> {{ model.api_base }}</p>
      <p><strong>API Key:</strong> {{ maskedKey }}</p>
    </div>
    <div class="model-actions">
      <button @click="$emit('edit', model)">编辑</button>
      <button @click="$emit('delete', model.id)">删除</button>
      <button v-if="!isActive" @click="$emit('activate', model.id)">激活</button>
      <span v-else class="active-badge">使用中</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ModelConfig } from '@/stores/models'

const props = defineProps<{
  model: ModelConfig
  isActive: boolean
}>()

defineEmits<{
  edit: [model: ModelConfig]
  delete: [id: string]
  activate: [id: string]
}>()

const maskedKey = computed(() => {
  const key = props.model.api_key
  if (key.length <= 8) return '***'
  return key.slice(0, 4) + '...' + key.slice(-4)
})
</script>

<style scoped>
.model-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.model-card.active {
  border: 2px solid #4CAF50;
}
.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.provider {
  background: #e0e0e0;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.model-body p {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
}
.model-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}
button {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
button:first-child {
  background: #2196F3;
  color: white;
}
button:nth-child(2) {
  background: #f44336;
  color: white;
}
.active-badge {
  background: #4CAF50;
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
}
</style>