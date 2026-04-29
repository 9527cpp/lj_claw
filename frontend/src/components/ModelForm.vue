<template>
  <div class="model-form-overlay" @click.self="$emit('close')">
    <div class="model-form">
      <h2>{{ editingModel ? '编辑模型' : '添加模型' }}</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>模型 ID</label>
          <input v-model="form.id" placeholder="如: gpt-4" required :disabled="!!editingModel" />
        </div>
        <div class="form-group">
          <label>名称</label>
          <input v-model="form.name" placeholder="如: GPT-4" required />
        </div>
        <div class="form-group">
          <label>Provider</label>
          <select v-model="form.provider" required>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
          </select>
        </div>
        <div class="form-group">
          <label>API Base URL</label>
          <input v-model="form.api_base" placeholder="https://api.openai.com/v1" required />
        </div>
        <div class="form-group">
          <label>API Key</label>
          <input v-model="form.api_key" type="password" placeholder="sk-..." required />
        </div>
        <div class="form-actions">
          <button type="button" @click="$emit('close')">取消</button>
          <button type="submit">{{ editingModel ? '保存' : '添加' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import type { ModelConfig } from '@/stores/models'

const props = defineProps<{
  editingModel?: ModelConfig
}>()

const emit = defineEmits<{
  close: []
  submit: [data: Partial<ModelConfig>]
}>()

const form = reactive({
  id: props.editingModel?.id || '',
  name: props.editingModel?.name || '',
  provider: props.editingModel?.provider || 'openai',
  api_base: props.editingModel?.api_base || '',
  api_key: props.editingModel?.api_key || ''
})

function handleSubmit() {
  emit('submit', { ...form })
}
</script>

<style scoped>
.model-form-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.model-form {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 400px;
}
h2 { margin-bottom: 16px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; margin-bottom: 4px; font-weight: 500; }
.form-group input, .form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 16px;
}
.form-actions button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.form-actions button[type="submit"] {
  background: #4CAF50;
  color: white;
}
</style>