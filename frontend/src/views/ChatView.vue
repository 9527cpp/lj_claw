<template>
  <div class="chat-view">
    <main class="chat-main">
      <div class="messages" ref="messagesEl">
        <div v-if="chatStore.messages.length === 0" class="welcome">
          <h2>欢迎使用 lj_claw Agent</h2>
          <p>开始对话吧</p>
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
        <input
          v-model="inputMessage"
          placeholder="输入消息..."
          :disabled="chatStore.loading"
          @keydown.enter="handleSend"
        />
        <button @click="handleSend" :disabled="chatStore.loading || !inputMessage.trim()">
          发送
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatMessage from '@/components/ChatMessage.vue'

const chatStore = useChatStore()
const inputMessage = ref('')
const messagesEl = ref<HTMLElement>()
const bottomEl = ref<HTMLElement>()

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

// Watch for messages changes to scroll to bottom
watch(() => chatStore.messages.length, async () => {
  await nextTick()
  scrollToBottom()
})

async function handleSend() {
  const msg = inputMessage.value.trim()
  if (!msg || chatStore.loading) return

  inputMessage.value = ''
  await chatStore.sendMessage(msg)

  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

async function handleRepeat(content: string) {
  await chatStore.sendMessage(content)
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-view { display: flex; flex-direction: column; height: 100vh; }
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 16px;
}
.welcome {
  text-align: center;
  color: #999;
  margin-top: 100px;
}
.welcome h2 { margin-bottom: 8px; }
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
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}
.input-area input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 24px;
  outline: none;
}
.input-area input:focus { border-color: #2196F3; }
.input-area button {
  padding: 12px 24px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 24px;
  cursor: pointer;
}
@media (max-width: 768px) {
  .chat-main { padding: 16px; }
  .input-area input { padding: 10px 14px; }
  .input-area button { padding: 10px 16px; }
}
</style>