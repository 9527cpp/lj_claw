<template>
  <div class="chat-message" :class="message.role">
    <div class="message-content" v-html="renderedContent"></div>
    <div class="message-actions">
      <button
        v-if="message.role === 'user'"
        class="action-btn repeat-btn"
        :class="{ repeating: isRepeating }"
        @click="handleRepeat"
        title="重新发送"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="23 4 23 10 17 10"></polyline>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
        </svg>
      </button>
      <button
        v-if="message.role === 'assistant'"
        class="action-btn copy-btn"
        :class="{ copied }"
        @click="copyMessage"
        :title="copied ? '已复制' : '复制'"
      >
        <svg v-if="!copied" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { marked } from 'marked'
import type { Message } from '@/stores/chat'

const props = defineProps<{ message: Message }>()
const emit = defineEmits<{ (e: 'repeat', content: string): void }>()

const copied = ref(false)
const isRepeating = ref(false)

const renderedContent = computed(() => {
  return marked.parse(props.message.content)
})

function handleRepeat() {
  isRepeating.value = true
  emit('repeat', props.message.content)
  setTimeout(() => { isRepeating.value = false }, 1000)
}

function copyMessage() {
  const text = props.message.content
  if (!text) {
    console.warn('Empty message content')
    return
  }

  // 优先使用 Clipboard API
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      copied.value = true
      setTimeout(() => { copied.value = false }, 1000)
    }).catch((err) => {
      console.error('Clipboard API failed:', err)
      fallbackCopy(text)
    })
  } else {
    fallbackCopy(text)
  }
}

function fallbackCopy(text: string) {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    document.execCommand('copy')
    copied.value = true
    setTimeout(() => { copied.value = false }, 1000)
  } catch (err) {
    console.error('Fallback copy failed:', err)
  }
  document.body.removeChild(textarea)
}
</script>

<style scoped>
.chat-message {
  display: flex;
  margin-bottom: 16px;
  align-items: flex-start;
  gap: 8px;
}
.chat-message.user { justify-content: flex-end; }
.chat-message.assistant { justify-content: flex-start; }
.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}
.message-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}
.chat-message:hover .message-actions {
  opacity: 1;
}
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.15s, color 0.15s;
}
.user .action-btn {
  background: #f0f0f0;
  color: #666;
}
.user .action-btn:hover {
  background: #e0e0e0;
  color: #333;
}
.user .action-btn.repeating {
  background: #cc785c;
  color: white;
}
.assistant .action-btn {
  background: #f0f0f0;
  color: #666;
}
.assistant .action-btn.copied {
  background: #4caf50;
  color: white;
}
.assistant .action-btn:hover {
  background: #e0e0e0;
  color: #333;
}
.user .message-content {
  background: #cc785c;
  color: white;
  border-bottom-right-radius: 4px;
}
.assistant .message-content {
  background: #faf9f5;
  color: #141413;
  border-bottom-left-radius: 4px;
  box-shadow: none;
}
.assistant .message-content :deep(pre) {
  background: #181715;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}
.assistant .message-content :deep(code) {
  background: #181715;
  color: #faf9f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 0.9em;
}
.assistant .message-content :deep(pre code) {
  background: none;
  padding: 0;
}
.assistant .message-content :deep(p) {
  margin: 8px 0;
}
.assistant .message-content :deep(p:first-child) {
  margin-top: 0;
}
.assistant .message-content :deep(p:last-child) {
  margin-bottom: 0;
}
.assistant .message-content :deep(ul), .assistant .message-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}
.assistant .message-content :deep(strong) {
  font-weight: 600;
}
</style>
