import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchHistory() {
    try {
      const res = await fetch('/api/chat/history')
      const data = await res.json()
      messages.value = data.history || []
    } catch (e) {
      console.error('Failed to fetch history:', e)
    }
  }

  async function sendMessage(content: string, modelId?: string) {
    loading.value = true
    error.value = null

    messages.value.push({ role: 'user', content })

    try {
      const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, model_id: modelId })
      })

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let assistantMessage = ''
      let assistantStarted = false

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
                if (!assistantStarted) {
                  messages.value.push({ role: 'assistant', content: assistantMessage })
                  assistantStarted = true
                } else {
                  // 更新最后一条 assistant 消息
                  const lastIdx = messages.value.length - 1
                  if (lastIdx >= 0 && messages.value[lastIdx].role === 'assistant') {
                    messages.value[lastIdx] = { role: 'assistant', content: assistantMessage }
                  }
                }
              } else if (data.type === 'error') {
                error.value = data.content
              }
            } catch {}
          }
        }
      }
    } catch (e: any) {
      error.value = e.message || '发送失败'
    } finally {
      loading.value = false
    }
  }

  async function clearHistory() {
    try {
      await fetch('/api/chat/history', { method: 'DELETE' })
      messages.value = []
    } catch (e) {
      console.error('Failed to clear history:', e)
    }
  }

  return { messages, loading, error, fetchHistory, sendMessage, clearHistory }
})
