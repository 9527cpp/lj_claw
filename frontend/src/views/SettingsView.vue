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

        <div v-if="skillsStore.importSources.length > 0" class="import-sources">
          <h3>已导入的路径</h3>
          <div v-for="src in skillsStore.importSources" :key="src.source" class="import-source-item">
            <div class="source-header">
              <div class="source-info">
                <span class="source-type">{{ getTypeLabel(src.type) }}</span>
                <span class="source-path" :title="src.source">{{ truncatePath(src.source) }}</span>
                <span class="source-count">{{ src.skills.length }} 个 skills</span>
              </div>
              <button class="unimport-btn" @click="handleUnimport(src.source)">
                取消导入
              </button>
            </div>
            <div class="source-search">
              <input
                v-model="searchTerms[src.source]"
                :placeholder="'搜索 ' + src.skills.length + ' 个 skills...'"
                class="search-input"
              />
            </div>
            <div class="source-skills">
              <span
                v-for="skill in filteredImportedSkills(src)"
                :key="skill.id"
                class="skill-tag"
                :class="{ enabled: isSkillEnabled(skill.id) }"
                @click="toggleImportedSkill(skill.id)"
                :title="isSkillEnabled(skill.id) ? '点击禁用' : '点击启用'"
              >
                {{ skill.name }}
              </span>
              <span v-if="filteredImportedSkills(src).length === 0 && searchTerms[src.source]" class="no-results">
                无匹配结果
              </span>
            </div>
          </div>
        </div>

        <div v-if="skillsLoading" class="loading">加载中...</div>
        <div v-else class="skills-list">
          <SkillToggle
            v-for="skill in filteredSkills"
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
import { ref, computed, onMounted } from 'vue'
import { useModelsStore } from '@/stores/models'
import { useSkillsStore } from '@/stores/skills'
import ModelCard from '@/components/ModelCard.vue'
import ModelForm from '@/components/ModelForm.vue'
import SkillToggle from '@/components/SkillToggle.vue'
import type { ModelConfig } from '@/stores/models'
import type { ImportSource } from '@/stores/skills'

const modelsStore = useModelsStore()
const skillsStore = useSkillsStore()
const loading = ref(false)
const skillsLoading = ref(false)
const showAddForm = ref(false)
const editingModel = ref<ModelConfig | undefined>()
const skillImportSource = ref('')
const importing = ref(false)
const importResult = ref<{ success: boolean; error?: string } | null>(null)

const importedSkillIds = computed(() => {
  const ids = new Set<string>()
  for (const src of skillsStore.importSources) {
    for (const skill of src.skills) {
      ids.add(skill.id)
    }
  }
  return ids
})

const filteredSkills = computed(() => {
  return skillsStore.skills.filter(s => !importedSkillIds.value.has(s.id))
})

onMounted(async () => {
  loading.value = true
  skillsLoading.value = true
  try {
    await Promise.all([
      modelsStore.fetchModels(),
      skillsStore.fetchSkills(),
      skillsStore.fetchImportSources()
    ])
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

async function handleUnimport(source: string) {
  if (!confirm('确定取消导入？该路径下所有 skills 将从列表中移除。')) return
  try {
    await skillsStore.unimportSkill(source)
  } catch (e: any) {
    alert('取消导入失败: ' + (e?.message || '未知错误'))
  }
}

const searchTerms = ref<Record<string, string>>({})

const filteredImportedSkills = computed(() => {
  return (src: ImportSource) => {
    const term = (searchTerms.value[src.source] || '').toLowerCase()
    if (!term) return src.skills
    return src.skills.filter((s: { name: string }) => s.name.toLowerCase().includes(term))
  }
})

function isSkillEnabled(skillId: string): boolean {
  const skill = skillsStore.skills.find(s => s.id === skillId)
  return skill?.enabled ?? false
}

async function toggleImportedSkill(skillId: string) {
  const skill = skillsStore.skills.find(s => s.id === skillId)
  if (skill) {
    await skillsStore.toggleSkill(skillId, !skill.enabled)
  }
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    symlink: '符号链接',
    copy: '复制',
    download: '下载',
    clone: '克隆',
    directory: '目录',
    batch: '批量'
  }
  return labels[type] || type
}

function truncatePath(path: string): string {
  if (path.length > 40) {
    return '...' + path.slice(-37)
  }
  return path
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
  flex-wrap: wrap;
}
.skill-import input {
  flex: 1;
  min-width: 150px;
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
.skill-import .error { color: #f44336; }

.import-sources {
  background: #f8f8f8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.import-sources h3 {
  margin-bottom: 12px;
  font-size: 14px;
  color: #666;
}
.import-source-item {
  background: white;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}
.import-source-item:last-child { margin-bottom: 0; }
.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.source-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.source-type {
  background: #e3f2fd;
  color: #1976D2;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  flex-shrink: 0;
}
.source-path {
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.unimport-btn {
  padding: 4px 12px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  flex-shrink: 0;
}
.unimport-btn:hover { background: #d32f2f; }
.source-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.skill-tag {
  background: #e0e0e0;
  color: #666;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}
.skill-tag.enabled {
  background: #4CAF50;
  color: white;
}
.skill-tag.enabled:hover {
  background: #388E3C;
}
.skill-tag:not(.enabled):hover {
  background: #bdbdbd;
}

.source-count {
  background: #e3f2fd;
  color: #1976D2;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-left: 8px;
}

.source-search {
  margin-bottom: 8px;
}

.search-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 12px;
}

.search-input:focus {
  outline: none;
  border-color: #2196F3;
}

.no-results {
  color: #999;
  font-size: 12px;
  padding: 4px;
}

@media (max-width: 768px) {
  .content { padding: 16px; }
  .skill-import { flex-direction: column; }
  .skill-import input { width: 100%; }
  .skill-import button { width: 100%; }
  .import-sources { padding: 12px; }
  .source-header { flex-direction: column; align-items: flex-start; gap: 8px; }
  .unimport-btn { width: 100%; }
}
</style>