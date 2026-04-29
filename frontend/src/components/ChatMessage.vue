<template>
  <div class="chat-message" :class="message.role">
    <div class="message-content">{{ message.content }}</div>
  </div>
</template>

<script setup lang="ts">
import type { Message } from '@/stores/chat'

defineProps<{ message: Message }>()
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
  line-height: 1.5;
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
</style>