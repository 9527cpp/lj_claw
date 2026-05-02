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
          <button type="button" class="cancel-btn" @click="$emit('close')">取消</button>
          <button type="submit" class="submit-btn">{{ editingModel ? '保存' : '添加' }}</button>
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
  background: rgba(20, 20, 19, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}
.model-form {
  background: #faf9f5;
  padding: 28px;
  border-radius: 12px;
  width: 420px;
  max-width: 95vw;
  border: 1px solid #e6dfd8;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}
h2 {
  font-size: 18px;
  font-weight: 600;
  color: #141413;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e6dfd8;
}
.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #3d3d3a;
}
.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e6dfd8;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  color: #141413;
  transition: border-color 0.2s;
}
.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #cc785c;
}
.form-group input:disabled {
  background: #f5f0e8;
  color: #6c6a64;
}
.form-group input::placeholder {
  color: #8e8b82;
}
.form-group select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236c6a64' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}
.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 24px;
}
.form-actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.cancel-btn {
  background: #f5f0e8;
  color: #6c6a64;
  border: 1px solid #e6dfd8;
}
.cancel-btn:hover {
  background: #e8e0d2;
  color: #3d3d3a;
}
.submit-btn {
  background: #cc785c;
  color: white;
}
.submit-btn:hover {
  background: #a9583e;
}
</style>