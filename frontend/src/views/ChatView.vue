<template>
  <div class="chat-view">
    <!-- Sessions sidebar -->
    <aside class="sessions-sidebar" :class="{ open: sessionsOpen }">
      <div class="sessions-header">
        <h3>对话历史</h3>
        <button class="new-session-btn" @click="handleNewSession" title="新建对话">
          <span>+</span>
        </button>
      </div>
      <div class="sessions-list">
        <div
          v-for="session in chatStore.sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.id === chatStore.activeSessionId }"
          @click="handleSwitchSession(session.id)"
        >
          <div class="session-info">
            <span class="session-name">{{ session.name }}</span>
            <span class="session-meta">{{ session.message_count }}条对话 · {{ formatTime(session.updated_at) }}</span>
          </div>
          <div class="session-actions">
            <button class="action-btn" @click.stop="handleRename(session)" title="重命名">✏️</button>
            <button class="action-btn delete" @click.stop="handleDelete(session.id)" title="删除">🗑️</button>
          </div>
        </div>
        <div v-if="chatStore.sessions.length === 0" class="no-sessions">
          暂无对话记录
        </div>
      </div>
    </aside>

    <!-- Mobile menu button -->
    <button class="mobile-sessions-btn" @click="sessionsOpen = !sessionsOpen">
      📋
    </button>

    <!-- Overlay -->
    <div class="overlay" v-if="sessionsOpen" @click="sessionsOpen = false"></div>

    <!-- Chat main -->
    <main class="chat-main">
      <div class="messages" ref="messagesEl">
        <div v-if="chatStore.messages.length === 0" class="welcome">
          <h2>欢迎使用 lj_claw Agent</h2>
          <p>开始对话吧</p>
          <p v-if="chatStore.activeSessionId" class="session-hint">
            当前对话: {{ currentSessionName }}
          </p>
        </div>
        <ChatMessage
          v-for="(msg, i) in chatStore.messages"
          :key="i"
          :message="msg"
          @repeat="handleRepeat"
        />
        <div ref="bottomEl"></div>
        <div v-if="chatStore.loading" class="loading-indicator">
          <span>思考中...</span>
        </div>
        <div v-if="chatStore.error" class="error-msg">
          {{ chatStore.error }}
        </div>
      </div>

      <div class="input-area">
        <div class="input-container">
          <div class="input-controls">
            <button
              class="search-toggle"
              :class="{ active: webSearchEnabled }"
              @click="webSearchEnabled = !webSearchEnabled"
              title="联网搜索"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <path d="m21 21-4.35-4.35"/>
              </svg>
              <span>联网</span>
            </button>
          </div>
          <div class="input-wrapper" :class="{ loading: chatStore.loading }">
            <input
              v-model="inputMessage"
              placeholder="输入消息，Enter 发送..."
              :disabled="chatStore.loading"
              @keydown.enter.exact.prevent="handleSend"
              ref="inputEl"
            />
            <button
              v-if="chatStore.loading"
              class="stop-btn"
              @click="handleCancel"
              title="停止生成"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatMessage from '@/components/ChatMessage.vue'

const chatStore = useChatStore()
const inputMessage = ref('')
const messagesEl = ref<HTMLElement>()
const bottomEl = ref<HTMLElement>()
const sessionsOpen = ref(false)
const inputEl = ref<HTMLInputElement>()

const currentSessionName = computed(() => {
  const session = chatStore.sessions.find(s => s.id === chatStore.activeSessionId)
  return session?.name || ''
})

function scrollToBottom() {
  if (bottomEl.value) {
    bottomEl.value.scrollIntoView({ behavior: 'smooth' })
  }
}

onMounted(async () => {
  await chatStore.fetchHistory()
  await nextTick()
  scrollToBottom()
})

watch(() => chatStore.messages.length, async () => {
  await nextTick()
  scrollToBottom()
})

const webSearchEnabled = ref(false)

async function handleSend() {
  const msg = inputMessage.value.trim()
  if (!msg || chatStore.loading) return

  inputMessage.value = ''
  await chatStore.sendMessage(msg, undefined, webSearchEnabled.value)

  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
  inputEl.value?.focus()
}

function handleCancel() {
  chatStore.cancel()
}

async function handleRepeat(content: string) {
  await chatStore.sendMessage(content)
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

async function handleNewSession() {
  await chatStore.createSession()
  sessionsOpen.value = false
}

async function handleSwitchSession(sessionId: string) {
  await chatStore.switchSession(sessionId)
  sessionsOpen.value = false
  await nextTick()
  scrollToBottom()
}

async function handleDelete(sessionId: string) {
  await chatStore.deleteSession(sessionId)
}

function handleRename(session: { id: string; name: string }) {
  const newName = prompt('输入新的对话名称:', session.name)
  if (newName && newName.trim()) {
    chatStore.renameSession(session.id, newName.trim())
  }
}

function formatTime(isoString: string): string {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`

  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow-x: hidden;
}

/* Sessions sidebar */
.sessions-sidebar {
  position: fixed;
  left: -280px;
  top: 0;
  bottom: 0;
  width: 280px;
  background: #faf9f5;
  border-right: 1px solid #e6dfd8;
  z-index: 110;
  transition: left 0.3s;
  display: flex;
  flex-direction: column;
}

.sessions-sidebar.open {
  left: 0;
}

@media (min-width: 769px) {
  .sessions-sidebar {
    left: 200px;
    z-index: 80;
  }

  .mobile-sessions-btn {
    display: none;
  }

  .overlay {
    display: none;
  }
}

.sessions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e6dfd8;
}

.sessions-header h3 {
  font-size: 16px;
  margin: 0;
}

.new-session-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #cc785c;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.new-session-btn:hover {
  background: #a9583e;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  border-left: 3px solid transparent;
  transition: background 0.15s;
}

.session-item:hover {
  background: #efe9de;
}

.session-item.active {
  background: transparent;
  border-left-color: #cc785c;
}

.session-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.session-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

.session-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 4px;
  border-radius: 4px;
}

.action-btn:hover {
  background: #e0e0e0;
}

.action-btn.delete:hover {
  background: #ffebee;
}

.no-sessions {
  text-align: center;
  color: #999;
  padding: 32px;
  font-size: 14px;
}

/* Mobile */
.mobile-sessions-btn {
  display: none;
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 120;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: white;
  border: 1px solid #e0e0e0;
  cursor: pointer;
  font-size: 18px;
}

.overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 160;
}

@media (max-width: 768px) {
  .mobile-sessions-btn {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .overlay {
    display: block;
  }

  .sessions-sidebar {
    left: -280px;
    z-index: 170;
  }

  .sessions-sidebar.open {
    left: 0;
  }
}

/* Chat main */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
  box-sizing: border-box;
  overflow-x: hidden;
}

@media (min-width: 769px) {
  .chat-main {
    margin-left: 480px;
  }
}

@media (max-width: 768px) {
  .chat-main {
    padding: 16px;
    padding-top: 70px;
  }
}

.messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: 16px;
}

.welcome {
  text-align: center;
  color: #999;
  margin-top: 100px;
}

.welcome h2 { margin-bottom: 8px; }

.session-hint {
  margin-top: 16px;
  font-size: 12px;
  color: #2196F3;
}

.loading-indicator {
  text-align: center;
  color: #999;
  padding: 8px;
}

.error-msg {
  background: #ffebee;
  color: #c62828;
  padding: 8px 16px;
  border-radius: 4px;
  margin: 8px 0;
}

.input-area {
  display: flex;
  padding-top: 16px;
  padding-bottom: 24px;
  padding-left: 24px;
  padding-right: 24px;
}

.input-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.input-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 4px;
}

.search-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 16px;
  border: 1.5px solid #e0e0e0;
  background: white;
  color: #999;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.search-toggle:hover {
  border-color: #2196F3;
  color: #2196F3;
}

.search-toggle.active {
  border-color: #2196F3;
  background: #e3f2fd;
  color: #1976D2;
}

.search-toggle svg {
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  align-items: center;
  background: #faf9f5;
  border: 1.5px solid #e6dfd8;
  border-radius: 24px;
  padding: 0 6px 0 20px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: #cc785c;
  box-shadow: 0 0 0 3px rgba(204, 120, 92, 0.08);
}

.input-wrapper input {
  flex: 1;
  border: none;
  outline: none;
  padding: 14px 0;
  font-size: 15px;
  background: transparent;
  color: #141413;
  min-width: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.input-wrapper input::placeholder {
  color: #6c6a64;
}

.input-wrapper input:disabled {
  color: #6c6a64;
  cursor: not-allowed;
}

.stop-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #efe9de;
  border: 1px solid #e6dfd8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3d3d3a;
  flex-shrink: 0;
  transition: all 0.15s;
}

.stop-btn:hover {
  background: #ffebee;
  border-color: #c64545;
  color: #c64545;
}

@media (max-width: 768px) {
  .input-area {
    padding: 12px 16px;
    padding-bottom: 24px;
  }

  .input-container {
    gap: 8px;
  }

  .input-wrapper {
    border-radius: 20px;
    padding: 0 6px 0 16px;
  }

  .input-wrapper input {
    padding: 12px 0;
    font-size: 15px;
  }

  .search-toggle {
    padding: 4px 10px;
    font-size: 12px;
  }

  .search-toggle span {
    display: none;
  }
}
</style>