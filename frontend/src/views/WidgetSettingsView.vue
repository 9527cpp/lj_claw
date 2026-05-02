<template>
  <div class="widget-settings">
    <main class="content">
      <div class="page-header">
        <h2>网站接入管理</h2>
        <button class="add-btn" @click="showAddForm = true">+ 添加网站</button>
      </div>

      <div v-if="widgetStore.loading" class="loading">加载中...</div>
      <div v-else-if="widgetStore.sites.length === 0" class="empty-state">
        <div class="empty-icon">🌐</div>
        <p>暂无接入网站</p>
        <p class="sub">点击上方按钮添加第一个网站，开始变现之旅</p>
      </div>

      <div v-else class="sites-list">
        <div v-for="site in widgetStore.sites" :key="site.id" class="site-card">
          <div class="site-header">
            <div class="site-info">
              <span class="site-name" :class="{ disabled: !site.enabled }">{{ site.site_name }}</span>
              <span class="site-url">{{ site.site_url }}</span>
            </div>
            <div class="site-status">
              <span class="status-dot" :class="{ active: site.enabled }"></span>
              <span class="status-text">{{ site.enabled ? '已启用' : '已禁用' }}</span>
            </div>
          </div>

          <div class="site-config">
            <div class="config-row">
              <span class="config-label">机器人名称</span>
              <span class="config-value">{{ site.bot_name }}</span>
            </div>
            <div class="config-row">
              <span class="config-label">主色调</span>
              <span class="config-value">
                <span class="color-swatch" :style="{ background: site.primary_color }"></span>
                {{ site.primary_color }}
              </span>
            </div>
          </div>

          <div class="site-key">
            <span class="key-label">API Key</span>
            <div class="key-value">
              <code>{{ site.api_key }}</code>
              <button class="icon-btn" @click="handleRegenerateKey(site.id)" title="重新生成">
                🔄
              </button>
            </div>
          </div>

          <div class="site-embed">
            <span class="embed-label">嵌入代码</span>
            <div class="embed-code">
              <pre>{{ widgetStore.getEmbedCode(site) }}</pre>
              <button class="copy-btn" @click="copyEmbedCode(site)">
                {{ copiedSiteId === site.id ? '已复制' : '复制代码' }}
              </button>
            </div>
          </div>

          <div class="site-actions">
            <button class="action-btn edit" @click="openEditForm(site)">编辑</button>
            <button class="action-btn toggle" @click="toggleSite(site)">
              {{ site.enabled ? '禁用' : '启用' }}
            </button>
            <button class="action-btn delete" @click="handleDelete(site.id)">删除</button>
          </div>
        </div>
      </div>

      <!-- Add/Edit Form Modal -->
      <div v-if="showAddForm || editingSite" class="modal-overlay" @click.self="closeForm">
        <div class="modal-form">
          <h3>{{ editingSite ? '编辑网站' : '添加网站' }}</h3>
          <form @submit.prevent="handleSubmit">
            <div class="form-group">
              <label>网站名称</label>
              <input v-model="form.site_name" placeholder="例如：我的淘宝店" required />
            </div>
            <div class="form-group">
              <label>网站地址</label>
              <input v-model="form.site_url" placeholder="https://www.example.com" required />
            </div>
            <div class="form-group">
              <label>机器人名称</label>
              <input v-model="form.bot_name" placeholder="店小二" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>主色调</label>
                <div class="color-input">
                  <input type="color" v-model="form.primary_color" />
                  <span>{{ form.primary_color }}</span>
                </div>
              </div>
              <div class="form-group">
                <label>次色调</label>
                <div class="color-input">
                  <input type="color" v-model="form.secondary_color" />
                  <span>{{ form.secondary_color }}</span>
                </div>
              </div>
            </div>
            <div class="form-group">
              <label>欢迎语</label>
              <input v-model="form.welcome_message" placeholder="您好，请问有什么可以帮助您？" />
            </div>
            <div class="form-group">
              <label>输入框占位文字</label>
              <input v-model="form.input_placeholder" placeholder="输入消息..." />
            </div>
            <div class="form-actions">
              <button type="button" class="cancel-btn" @click="closeForm">取消</button>
              <button type="submit" class="submit-btn">
                {{ editingSite ? '保存' : '添加' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useWidgetStore, type WidgetSite } from '@/stores/widget'

const widgetStore = useWidgetStore()
const showAddForm = ref(false)
const editingSite = ref<WidgetSite | null>(null)
const copiedSiteId = ref<string | null>(null)

const form = reactive({
  site_name: '',
  site_url: '',
  bot_name: 'AI 客服',
  primary_color: '#cc785c',
  secondary_color: '#a9583e',
  welcome_message: '您好，有什么可以帮您的？',
  input_placeholder: '输入消息...',
  enabled: true
})

onMounted(async () => {
  await widgetStore.fetchSites()
})

function openEditForm(site: WidgetSite) {
  editingSite.value = site
  Object.assign(form, {
    site_name: site.site_name,
    site_url: site.site_url,
    bot_name: site.bot_name,
    primary_color: site.primary_color,
    secondary_color: site.secondary_color,
    welcome_message: site.welcome_message,
    input_placeholder: site.input_placeholder,
    enabled: site.enabled
  })
}

function closeForm() {
  showAddForm.value = false
  editingSite.value = null
  resetForm()
}

function resetForm() {
  Object.assign(form, {
    site_name: '',
    site_url: '',
    bot_name: 'AI 客服',
    primary_color: '#cc785c',
    secondary_color: '#a9583e',
    welcome_message: '您好，有什么可以帮您的？',
    input_placeholder: '输入消息...',
    enabled: true
  })
}

async function handleSubmit() {
  try {
    if (editingSite.value) {
      await widgetStore.updateSite(editingSite.value.id, { ...form })
    } else {
      await widgetStore.createSite({ ...form })
    }
    closeForm()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '操作失败')
  }
}

async function handleDelete(siteId: string) {
  if (!confirm('确定删除该网站接入？')) return
  try {
    await widgetStore.deleteSite(siteId)
  } catch (e: any) {
    alert(e?.response?.data?.detail || '删除失败')
  }
}

async function toggleSite(site: WidgetSite) {
  try {
    await widgetStore.updateSite(site.id, { ...site, enabled: !site.enabled })
  } catch (e: any) {
    alert('操作失败')
  }
}

async function handleRegenerateKey(siteId: string) {
  if (!confirm('确定重新生成 API Key？旧 Key 将立即失效。')) return
  try {
    await widgetStore.regenerateKey(siteId)
  } catch (e: any) {
    alert('操作失败')
  }
}

function copyEmbedCode(site: WidgetSite) {
  const code = widgetStore.getEmbedCode(site)
  navigator.clipboard.writeText(code).then(() => {
    copiedSiteId.value = site.id
    setTimeout(() => { copiedSiteId.value = null }, 2000)
  })
}
</script>

<style scoped>
.widget-settings {
  min-height: 100vh;
  background: #faf9f5;
}

.content {
  padding: 32px 40px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #141413;
}

.add-btn {
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

.loading {
  text-align: center;
  color: #6c6a64;
  padding: 40px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6c6a64;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-state p { font-size: 16px; margin-bottom: 8px; }
.empty-state .sub { font-size: 13px; color: #8e8b82; }

.sites-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.site-card {
  background: white;
  border-radius: 10px;
  padding: 20px;
  border: 1px solid #e6dfd8;
}

.site-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.site-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.site-name {
  font-size: 16px;
  font-weight: 600;
  color: #141413;
}
.site-name.disabled { color: #8e8b82; }

.site-url {
  font-size: 12px;
  color: #6c6a64;
}

.site-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c64545;
}
.status-dot.active { background: #5db872; }

.status-text {
  font-size: 12px;
  color: #6c6a64;
}

.site-config {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
  padding: 12px;
  background: #faf9f5;
  border-radius: 6px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-label {
  font-size: 12px;
  color: #6c6a64;
}

.config-value {
  font-size: 13px;
  color: #3d3d3a;
  display: flex;
  align-items: center;
  gap: 6px;
}

.color-swatch {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: 1px solid #e6dfd8;
}

.site-key {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.key-label {
  font-size: 12px;
  color: #6c6a64;
  flex-shrink: 0;
}

.key-value {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.key-value code {
  font-size: 11px;
  color: #3d3d3a;
  background: #f5f0e8;
  padding: 4px 8px;
  border-radius: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
}

.site-embed {
  margin-bottom: 12px;
}

.embed-label {
  font-size: 12px;
  color: #6c6a64;
  display: block;
  margin-bottom: 6px;
}

.embed-code {
  position: relative;
}

.embed-code pre {
  background: #181715;
  color: #faf9f5;
  padding: 12px;
  border-radius: 6px;
  font-size: 11px;
  font-family: 'SF Mono', Monaco, monospace;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 100px;
  overflow-y: auto;
}

.copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(250, 249, 245, 0.9);
  color: #faf9f5;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.site-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.action-btn {
  padding: 6px 14px;
  border: none;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.edit {
  background: #f5f0e8;
  color: #3d3d3a;
  border: 1px solid #e6dfd8;
}
.action-btn.edit:hover { background: #e8e0d2; }

.action-btn.toggle {
  background: #e3f2fd;
  color: #1976D2;
}
.action-btn.toggle:hover { background: #bbdefb; }

.action-btn.delete {
  background: #faf9f5;
  color: #c64545;
  border: 1px solid #c64545;
}
.action-btn.delete:hover {
  background: #c64545;
  color: white;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 19, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.modal-form {
  background: #faf9f5;
  padding: 28px;
  border-radius: 12px;
  width: 480px;
  max-width: 95vw;
  border: 1px solid #e6dfd8;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}

.modal-form h3 {
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
  font-size: 13px;
  font-weight: 500;
  color: #3d3d3a;
  margin-bottom: 6px;
}

.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e6dfd8;
  border-radius: 6px;
  font-size: 14px;
  color: #141413;
  background: white;
  transition: border-color 0.2s;
}
.form-group input:focus {
  outline: none;
  border-color: #cc785c;
}
.form-group input::placeholder { color: #8e8b82; }

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.color-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.color-input input[type="color"] {
  width: 40px;
  height: 36px;
  padding: 2px;
  border: 1px solid #e6dfd8;
  border-radius: 6px;
  cursor: pointer;
}

.color-input span {
  font-size: 13px;
  color: #6c6a64;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 24px;
}

.cancel-btn {
  padding: 10px 20px;
  background: #f5f0e8;
  color: #6c6a64;
  border: 1px solid #e6dfd8;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}
.cancel-btn:hover { background: #e8e0d2; }

.submit-btn {
  padding: 10px 20px;
  background: #cc785c;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}
.submit-btn:hover { background: #a9583e; }

@media (max-width: 768px) {
  .content { padding: 20px 16px; }
  .form-row { grid-template-columns: 1fr; }
  .site-config { flex-direction: column; gap: 8px; }
}
</style>