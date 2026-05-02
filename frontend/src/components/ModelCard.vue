<template>
  <div class="model-card" :class="{ active: isActive }">
    <div class="model-header">
      <h3>{{ model.name }}</h3>
      <span class="provider">{{ model.provider }}</span>
    </div>
    <div class="model-body">
      <p><strong>API Base:</strong> <span class="mono">{{ model.api_base }}</span></p>
      <p><strong>API Key:</strong> <span class="mono">{{ maskedKey }}</span></p>
    </div>
    <div class="model-actions">
      <button class="edit-btn" @click="$emit('edit', model)">编辑</button>
      <button class="delete-btn" @click="$emit('delete', model.id)">删除</button>
      <button v-if="!isActive" class="activate-btn" @click="$emit('activate', model.id)">激活</button>
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
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border: 1px solid #e6dfd8;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.model-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.model-card.active {
  border: 2px solid #cc785c;
}
.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.model-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #141413;
}
.provider {
  background: #f5f0e8;
  color: #6c6a64;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}
.model-body {
  margin-bottom: 14px;
}
.model-body p {
  margin: 6px 0;
  font-size: 13px;
  color: #6c6a64;
}
.model-body strong {
  color: #3d3d3a;
  font-weight: 500;
}
.mono {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  font-size: 12px;
  color: #3d3d3a;
}
.model-actions {
  margin-top: 14px;
  display: flex;
  gap: 8px;
  align-items: center;
}
button {
  padding: 7px 14px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}
.edit-btn {
  background: #f5f0e8;
  color: #3d3d3a;
  border: 1px solid #e6dfd8;
}
.edit-btn:hover {
  background: #e8e0d2;
}
.delete-btn {
  background: #faf9f5;
  color: #c64545;
  border: 1px solid #c64545;
}
.delete-btn:hover {
  background: #c64545;
  color: white;
}
.activate-btn {
  background: #cc785c;
  color: white;
}
.activate-btn:hover {
  background: #a9583e;
}
.active-badge {
  background: #5db8a6;
  color: white;
  padding: 7px 14px;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 500;
}
</style>