import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export interface Session {
  id: string
  name: string
  created_at: string
  updated_at: string
  message_count: number
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<Session[]>([])
  const activeSessionId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchSessions() {
    try {
      const res = await fetch('/api/chat/sessions')
      const data = await res.json()
      sessions.value = data.sessions || []
      activeSessionId.value = data.active_session
    } catch (e) {
      console.error('Failed to fetch sessions:', e)
    }
  }

  async function createSession(name?: string) {
    try {
      const res = await fetch('/api/chat/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      })
      const data = await res.json()
      await fetchSessions()
      if (data.session) {
        activeSessionId.value = data.session.id
        messages.value = []
      }
      return data.session
    } catch (e) {
      console.error('Failed to create session:', e)
    }
  }

  async function switchSession(sessionId: string) {
    try {
      // Set as active
      await fetch(`/api/chat/sessions/${sessionId}/active`, { method: 'PUT' })
      activeSessionId.value = sessionId

      // Load session messages
      const res = await fetch(`/api/chat/sessions/${sessionId}`)
      const data = await res.json()
      messages.value = data.session?.messages || []
    } catch (e) {
      console.error('Failed to switch session:', e)
    }
  }

  async function deleteSession(sessionId: string) {
    if (!confirm('确定删除该对话？')) return
    try {
      const res = await fetch(`/api/chat/sessions/${sessionId}`, { method: 'DELETE' })
      const data = await res.json()
      await fetchSessions()
      if (data.active_session && data.active_session !== activeSessionId.value) {
        await switchSession(data.active_session)
      } else if (sessions.value.length > 0) {
        await switchSession(sessions.value[0].id)
      } else {
        activeSessionId.value = null
        messages.value = []
      }
    } catch (e) {
      console.error('Failed to delete session:', e)
    }
  }

  async function renameSession(sessionId: string, name: string) {
    try {
      await fetch(`/api/chat/sessions/${sessionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      })
      await fetchSessions()
    } catch (e) {
      console.error('Failed to rename session:', e)
    }
  }

  async function fetchHistory() {
    await fetchSessions()
    if (activeSessionId.value) {
      await switchSession(activeSessionId.value)
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
        body: JSON.stringify({ message: content, model_id: modelId, session_id: activeSessionId.value })
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

      // Refresh sessions to update message counts
      await fetchSessions()
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
      await fetchSessions()
    } catch (e) {
      console.error('Failed to clear history:', e)
    }
  }

  return {
    sessions,
    activeSessionId,
    messages,
    loading,
    error,
    fetchSessions,
    createSession,
    switchSession,
    deleteSession,
    renameSession,
    fetchHistory,
    sendMessage,
    clearHistory
  }
})
