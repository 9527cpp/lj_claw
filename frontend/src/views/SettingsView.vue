<template>
  <div class="settings-view">
    <nav class="nav">
      <router-link to="/settings" class="nav-link active">Settings</router-link>
      <router-link to="/chat" class="nav-link">Chat</router-link>
    </nav>

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
</script>

<style scoped>
.settings-view { min-height: 100vh; }
.nav {
  background: white;
  padding: 0 24px;
  display: flex;
  gap: 24px;
  border-bottom: 1px solid #e0e0e0;
}
.nav-link {
  padding: 16px 0;
  color: #666;
  text-decoration: none;
  border-bottom: 2px solid transparent;
}
.nav-link.active { color: #2196F3; border-bottom-color: #2196F3; }
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
</style>