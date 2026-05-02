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

      <section class="ilink-section">
        <h2>微信连接 (ClawBot / iLink)</h2>
        <div class="ilink-card">
          <div class="ilink-status">
            <div class="status-row">
              <span class="status-label">Bridge 状态</span>
              <span class="status-value" :class="{ running: bridgeRunning }">
                {{ bridgeRunning ? '运行中' : '未运行' }}
              </span>
            </div>
            <div class="status-row">
              <span class="status-label">登录状态</span>
              <span class="status-value" :class="{ connected: hasToken }">
                {{ hasToken ? '已登录' : '未登录' }}
              </span>
            </div>
          </div>
          <button class="ilink-btn" @click="showQRModal = true">
            {{ hasToken ? '重新扫码登录' : '扫码登录' }}
          </button>
        </div>
      </section>
    </main>

    <ILinkQRModal
      :visible="showQRModal"
      @close="showQRModal = false"
      @login-success="onLoginSuccess"
    />

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
import ILinkQRModal from '@/components/ILinkQRModal.vue'
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
const showQRModal = ref(false)
const bridgeRunning = ref(false)
const hasToken = ref(false)

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
      skillsStore.fetchImportSources(),
      fetchILinkStatus(),
    ])
  } finally {
    loading.value = false
    skillsLoading.value = false
  }
})

async function fetchILinkStatus() {
  try {
    const [statusRes, tokenRes] = await Promise.all([
      fetch('/api/ilink/status'),
      fetch('/api/ilink/token'),
    ])
    const statusData = await statusRes.json()
    const tokenData = await tokenRes.json()
    bridgeRunning.value = statusData.running || false
    hasToken.value = tokenData.exists || false
  } catch {
    // ignore
  }
}

function onLoginSuccess() {
  hasToken.value = true
  bridgeRunning.value = true
}

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
.settings-view {
  min-height: 100vh;
  background: #faf9f5;
}

.content {
  padding: 32px 40px;
  max-width: 900px;
  margin: 0 auto;
}

section {
  margin-bottom: 40px;
}

h2 {
  font-family: 'Inter', sans-serif;
  font-size: 20px;
  font-weight: 600;
  color: #141413;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e6dfd8;
}

/* Models Section */
.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.empty, .loading {
  color: #6c6a64;
  text-align: center;
  padding: 40px;
  font-size: 14px;
}

.add-btn {
  margin-top: 16px;
  padding: 10px 20px;
  background: #cc785c;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.add-btn:hover { background: #a9583e; }

/* Skills Section */
.skill-import {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  align-items: center;
  flex-wrap: wrap;
}
.skill-import input {
  flex: 1;
  min-width: 200px;
  padding: 10px 14px;
  border: 1px solid #e6dfd8;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  color: #141413;
}
.skill-import input::placeholder { color: #8e8b82; }
.skill-import input:focus {
  outline: none;
  border-color: #cc785c;
}
.skill-import button {
  padding: 10px 20px;
  background: #5db8a6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.skill-import button:hover { background: #4a9d8c; }
.skill-import button:disabled {
  background: #e6dfd8;
  color: #8e8b82;
  cursor: not-allowed;
}
.skill-import .success { color: #5db872; font-size: 13px; }
.skill-import .error { color: #c64545; font-size: 13px; }

/* Import Sources */
.import-sources {
  background: #f5f0e8;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
}
.import-sources h3 {
  margin-bottom: 16px;
  font-size: 13px;
  font-weight: 600;
  color: #6c6a64;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.import-source-item {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #ebe6df;
}
.import-source-item:last-child { margin-bottom: 0; }

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}
.source-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.source-type {
  background: #e8e0d2;
  color: #6c6a64;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}
.source-path {
  font-size: 12px;
  color: #6c6a64;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.source-count {
  background: #e8e0d2;
  color: #6c6a64;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  margin-left: 8px;
  flex-shrink: 0;
}
.unimport-btn {
  padding: 6px 14px;
  background: #faf9f5;
  color: #c64545;
  border: 1px solid #c64545;
  border-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
  transition: all 0.2s;
}
.unimport-btn:hover {
  background: #c64545;
  color: white;
}

.source-search {
  margin-bottom: 12px;
}
.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ebe6df;
  border-radius: 5px;
  font-size: 13px;
  background: #faf9f5;
  color: #141413;
}
.search-input:focus {
  outline: none;
  border-color: #cc785c;
}
.search-input::placeholder { color: #8e8b82; }

.source-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.skill-tag {
  background: #e6dfd8;
  color: #6c6a64;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.skill-tag:hover {
  background: #e8e0d2;
  color: #3d3d3a;
}
.skill-tag.enabled {
  background: #5db8a6;
  color: white;
  border-color: #4a9d8c;
}
.skill-tag.enabled:hover {
  background: #4a9d8c;
}

.no-results {
  color: #8e8b82;
  font-size: 12px;
  padding: 6px;
}

/* Skills List */
.skills-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* iLink Section */
.ilink-section {
  border-top: 1px solid #e6dfd8;
  padding-top: 32px;
  margin-top: 8px;
}
.ilink-card {
  background: white;
  border-radius: 10px;
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 480px;
  border: 1px solid #e6dfd8;
}
.ilink-status {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.status-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.status-label {
  font-size: 13px;
  color: #6c6a64;
  width: 72px;
}
.status-value {
  font-size: 13px;
  font-weight: 600;
  color: #8e8b82;
}
.status-value.running { color: #5db872; }
.status-value.connected { color: #07C160; }
.ilink-btn {
  padding: 10px 24px;
  background: #07C160;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s;
}
.ilink-btn:hover { background: #06a050; }

/* Responsive */
@media (max-width: 768px) {
  .content { padding: 20px 16px; }
  .skill-import { flex-direction: column; }
  .skill-import input { width: 100%; }
  .skill-import button { width: 100%; }
  .import-sources { padding: 16px; }
  .source-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .unimport-btn { width: 100%; }
  .ilink-card { flex-direction: column; align-items: flex-start; gap: 16px; }
  .models-grid { grid-template-columns: 1fr; }
}
</style>