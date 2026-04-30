<template>
  <div class="settings-view">
    <main class="content">
      <section class="models-section">
        <h2>模型配置</h2>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="modelsStore.models.length === 0" class="empty">
          <p>暂无模型配置</p>
        </div>
        <div v-else class="models-grid">
          <ModelCard
            v-for="model in modelsStore.models"
            :key="model.id"
            :model="model"
            :is-active="model.id === modelsStore.activeModel"
            @edit="openEditForm"
            @delete="handleDelete"
            @activate="handleActivate"
          />
        </div>
        <button class="add-btn" @click="showAddForm = true">+ 添加模型</button>
      </section>

      <section class="skills-section">
        <h2>Skills 管理</h2>
        <div class="skill-import">
          <input v-model="skillImportSource" placeholder="输入 URL 或本地路径导入 Skill" />
          <button @click="handleImportSkill" :disabled="importing">
            {{ importing ? '导入中...' : '导入' }}
          </button>
          <span v-if="importResult" :class="{ success: importResult.success, error: !importResult.success }">
            {{ importResult.success ? '导入成功' : importResult.error }}
          </span>
        </div>
        <div v-if="skillsLoading" class="loading">加载中...</div>
        <div v-else class="skills-list">
          <SkillToggle
            v-for="skill in skillsStore.skills"
            :key="skill.id"
            :skill="skill"
            @toggle="handleSkillToggle"
          />
        </div>
      </section>
    </main>

    <ModelForm
      v-if="showAddForm || editingModel"
      :editing-model="editingModel"
      @close="closeForm"
      @submit="handleFormSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useModelsStore } from '@/stores/models'
import { useSkillsStore } from '@/stores/skills'
import ModelCard from '@/components/ModelCard.vue'
import ModelForm from '@/components/ModelForm.vue'
import SkillToggle from '@/components/SkillToggle.vue'
import type { ModelConfig } from '@/stores/models'

const modelsStore = useModelsStore()
const skillsStore = useSkillsStore()
const loading = ref(false)
const skillsLoading = ref(false)
const showAddForm = ref(false)
const editingModel = ref<ModelConfig | undefined>()
const skillImportSource = ref('')
const importing = ref(false)
const importResult = ref<{ success: boolean; error?: string } | null>(null)

onMounted(async () => {
  loading.value = true
  skillsLoading.value = true
  try {
    await Promise.all([modelsStore.fetchModels(), skillsStore.fetchSkills()])
  } finally {
    loading.value = false
    skillsLoading.value = false
  }
})

function openEditForm(model: ModelConfig) {
  editingModel.value = model
}

function closeForm() {
  showAddForm.value = false
  editingModel.value = undefined
}

async function handleFormSubmit(data: Partial<ModelConfig>) {
  if (editingModel.value) {
    await modelsStore.updateModel(editingModel.value.id, data as ModelConfig)
  } else {
    await modelsStore.addModel(data as any)
  }
  closeForm()
}

async function handleDelete(id: string) {
  if (confirm('确定删除?')) {
    await modelsStore.deleteModel(id)
  }
}

async function handleActivate(id: string) {
  await modelsStore.setActive(id)
}

async function handleSkillToggle(id: string, enabled: boolean) {
  await skillsStore.toggleSkill(id, enabled)
}

async function handleImportSkill() {
  if (!skillImportSource.value.trim()) return
  importing.value = true
  importResult.value = null
  try {
    await skillsStore.importSkill(skillImportSource.value)
    importResult.value = { success: true }
    skillImportSource.value = ''
  } catch (e: any) {
    importResult.value = { success: false, error: e?.response?.data?.detail || '导入失败' }
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.settings-view { min-height: 100vh; }
.content { padding: 24px; max-width: 800px; margin: 0 auto; }
section { margin-bottom: 32px; }
h2 { margin-bottom: 16px; }
.models-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.empty, .loading { color: #999; text-align: center; padding: 32px; }
.add-btn {
  margin-top: 16px;
  padding: 12px 24px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.skill-import {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  align-items: center;
}
.skill-import input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.skill-import button {
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.skill-import button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
.skill-import .success { color: #4CAF50; }
@media (max-width: 768px) {
  .content { padding: 16px; }
  .skill-import { flex-direction: column; }
  .skill-import input { width: 100%; }
  .skill-import button { width: 100%; }
}
</style>