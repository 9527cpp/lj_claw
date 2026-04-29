<template>
  <div class="chat-message" :class="message.role">
    <div class="message-content" v-html="renderedContent"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { Message } from '@/stores/chat'

const props = defineProps<{ message: Message }>()

const renderedContent = computed(() => {
  return marked.parse(props.message.content)
})
</script>

<style scoped>
.chat-message {
  display: flex;
  margin-bottom: 16px;
}
.chat-message.user { justify-content: flex-end; }
.chat-message.assistant { justify-content: flex-start; }
.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}
.user .message-content {
  background: #2196F3;
  color: white;
  border-bottom-right-radius: 4px;
}
.assistant .message-content {
  background: white;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}
.assistant .message-content :deep(pre) {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}
.assistant .message-content :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
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
