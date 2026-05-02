<template>
  <div class="widget-chat" :class="{ 'widget-minimized': minimized }">
    <!-- Chat Toggle Button (shown when minimized) -->
    <button
      v-if="minimized"
      class="widget-toggle"
      @click="minimized = false"
      :style="{ background: primaryColor }"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
      <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
    </button>

    <!-- Chat Window (shown when open) -->
    <div v-else class="widget-window">
      <!-- Header -->
      <div class="widget-header" :style="{ background: primaryColor }">
        <div class="header-info">
          <div class="avatar" :style="{ background: secondaryColor }">
            {{ botName ? botName[0] : 'AI' }}
          </div>
          <div class="header-text">
            <span class="bot-name">{{ botName }}</span>
            <span class="status">在线 · 随时为您服务</span>
          </div>
        </div>
        <button class="minimize-btn" @click="minimized = true">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </button>
      </div>

      <!-- Messages Area -->
      <div class="widget-messages" ref="messagesEl">
        <div v-if="messages.length === 0" class="welcome-msg">
          <p>您好！我是 {{ botName }}，有什么可以帮您的？</p>
        </div>
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="msg-item"
          :class="msg.role"
        >
          <div class="msg-bubble" v-html="renderMarkdown(msg.content)"></div>
        </div>
        <div v-if="loading" class="msg-item assistant">
          <div class="msg-bubble typing">
            <span></span><span></span><span></span>
          </div>
        </div>
        <div ref="bottomEl"></div>
      </div>

      <!-- Input Area -->
      <div class="widget-input">
        <input
          v-model="inputText"
          :placeholder="inputPlaceholder"
          @keydown.enter.prevent="sendMessage"
          :disabled="loading"
        />
        <button
          @click="sendMessage"
          :disabled="!inputText.trim() || loading"
          :style="{ background: primaryColor }"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { marked } from 'marked'

interface WidgetConfig {
  primaryColor?: string
  secondaryColor?: string
  botName?: string
  welcomeMessage?: string
  inputPlaceholder?: string
}

const props = defineProps<{
  config?: WidgetConfig
}>()

const cfg = computed(() => props.config || {})

const primaryColor = computed(() => cfg.value.primaryColor || '#cc785c')
const secondaryColor = computed(() => cfg.value.secondaryColor || '#a9583e')
const botName = computed(() => cfg.value.botName || 'AI 客服')
const inputPlaceholder = computed(() => cfg.value.inputPlaceholder || '输入消息...')

const minimized = ref(false)
const messages = ref<{ role: 'user' | 'assistant'; content: string }[]>([])
const inputText = ref('')
const loading = ref(false)
const unreadCount = ref(0)
const messagesEl = ref<HTMLElement>()
const bottomEl = ref<HTMLElement>()

function renderMarkdown(text: string) {
  return marked.parse(text) as string
}

function scrollToBottom() {
  nextTick(() => {
    if (bottomEl.value) {
      bottomEl.value.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  loading.value = true
  scrollToBottom()

  try {
    const res = await fetch('/api/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    })

    const reader = res.body?.getReader()
    if (!reader) throw new Error('No response body')

    const decoder = new TextDecoder()
    let assistantMessage = ''

    messages.value.push({ role: 'assistant', content: '' })

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'text') {
              assistantMessage += data.content
              const lastIdx = messages.value.length - 1
              if (lastIdx >= 0) {
                messages.value[lastIdx] = { role: 'assistant', content: assistantMessage }
              }
              scrollToBottom()
            }
          } catch {}
        }
      }
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '抱歉，服务出现问题，请稍后再试。' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

watch(minimized, (val) => {
  if (!val) unreadCount.value = 0
})
</script>

<style scoped>
.widget-chat {
  position: fixed;
  z-index: 999999;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  bottom: 20px;
  right: 20px;
}

.widget-toggle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
  position: relative;
  transition: transform 0.2s, box-shadow 0.2s;
}

.widget-toggle:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}

.unread-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: #c64545;
  color: white;
  font-size: 11px;
  font-weight: 600;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.widget-window {
  width: 360px;
  height: 520px;
  max-height: 80vh;
  background: #faf9f5;
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #e6dfd8;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  color: white;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  color: white;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.bot-name {
  font-size: 15px;
  font-weight: 600;
}

.status {
  font-size: 11px;
  opacity: 0.85;
}

.minimize-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.minimize-btn:hover {
  background: rgba(255,255,255,0.15);
}

.widget-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome-msg {
  text-align: center;
  color: #6c6a64;
  padding: 24px 16px;
  font-size: 14px;
  line-height: 1.5;
}

.msg-item {
  display: flex;
  flex-direction: column;
}

.msg-item.user {
  align-items: flex-end;
}

.msg-item.assistant {
  align-items: flex-start;
}

.msg-bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
  overflow-x: hidden;
}

.user .msg-bubble {
  background: #cc785c;
  color: white;
  border-bottom-right-radius: 4px;
}

.assistant .msg-bubble {
  background: white;
  color: #141413;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.msg-bubble :deep(p) { margin: 4px 0; }
.msg-bubble :deep(p:first-child) { margin-top: 0; }
.msg-bubble :deep(p:last-child) { margin-bottom: 0; }
.msg-bubble :deep(code) {
  background: #181715;
  color: #faf9f5;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 12px;
}
.msg-bubble :deep(pre) {
  background: #181715;
  padding: 8px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 6px 0;
}
.msg-bubble :deep(pre code) {
  background: none;
  padding: 0;
}

.typing {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.typing span {
  width: 8px;
  height: 8px;
  background: #6c6a64;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

.widget-input {
  display: flex;
  gap: 8px;
  padding: 12px 14px;
  border-top: 1px solid #e6dfd8;
  background: white;
}

.widget-input input {
  flex: 1;
  border: 1px solid #e6dfd8;
  border-radius: 20px;
  padding: 10px 16px;
  font-size: 14px;
  outline: none;
  color: #141413;
  background: #faf9f5;
  transition: border-color 0.2s;
}

.widget-input input:focus {
  border-color: #cc785c;
}

.widget-input input::placeholder {
  color: #8e8b82;
}

.widget-input input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.widget-input button {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s, opacity 0.15s;
  flex-shrink: 0;
}

.widget-input button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.widget-input button:not(:disabled):hover {
  transform: scale(1.05);
}

@media (max-width: 480px) {
  .widget-chat {
    bottom: 12px;
    right: 12px;
  }

  .widget-window {
    width: calc(100vw - 24px);
    height: calc(100vh - 80px);
    max-height: 600px;
  }
}
</style>