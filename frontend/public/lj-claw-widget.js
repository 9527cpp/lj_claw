/**
 * lj_claw Widget Loader
 * 
 * Embed code:
 * <script src="https://your-domain.com/lj-claw-widget.js"></script>
 * <script>
 *   LjClawWidget.init({
 *     apiUrl: 'https://your-domain.com/api/chat/',
 *     botName: '店小二',
 *     primaryColor: '#cc785c',
 *     welcomeMessage: '您好，请问有什么可以帮助您？'
 *   })
 * </script>
 */

(function () {
  'use strict';

  // Prevent multiple initializations
  if (window.LjClawWidget && window.LjClawWidget.initialized) {
    console.warn('[lj_claw] Widget already initialized')
    return
  }

  const CONFIG_KEY = 'lj_claw_widget_config'
  const INSTANCE_KEY = 'lj_claw_widget_instance'

  // Merge user config with defaults
  function getConfig(opts) {
    return Object.assign({
      apiUrl: '',
      botName: 'AI 客服',
      primaryColor: '#cc785c',
      secondaryColor: '#a9583e',
      welcomeMessage: '您好，有什么可以帮您的？',
      inputPlaceholder: '输入消息...',
      position: 'bottom-right', // bottom-right | bottom-left
      offsetX: 20,
      offsetY: 20
    }, opts)
  }

  // Create widget HTML
  function createWidgetHTML(config) {
    return `
      <div class="lj-claw-widget ${config.position}" id="lj-claw-widget">
        <!-- Toggle Button -->
        <button class="lj-claw-toggle" id="lj-claw-toggle" aria-label="打开客服">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <span class="lj-claw-badge" id="lj-claw-badge" style="display:none">0</span>
        </button>

        <!-- Chat Window -->
        <div class="lj-claw-window" id="lj-claw-window" style="display:none">
          <!-- Header -->
          <div class="lj-claw-header">
            <div class="lj-claw-header-info">
              <div class="lj-claw-avatar" style="background:${config.secondaryColor}">${config.botName[0] || 'AI'}</div>
              <div class="lj-claw-header-text">
                <span class="lj-claw-bot-name">${config.botName}</span>
                <span class="lj-claw-status">在线 · 随时为您服务</span>
              </div>
            </div>
            <button class="lj-claw-minimize" id="lj-claw-minimize" aria-label="最小化">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </button>
          </div>

          <!-- Messages -->
          <div class="lj-claw-messages" id="lj-claw-messages">
            <div class="lj-claw-welcome">
              <p>${config.welcomeMessage}</p>
            </div>
          </div>

          <!-- Input -->
          <div class="lj-claw-input-area">
            <input type="text" class="lj-claw-input" id="lj-claw-input"
              placeholder="${config.inputPlaceholder}" />
            <button class="lj-claw-send" id="lj-claw-send">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
        </div>
      </div>
    `
  }

  // Inject styles
  function injectStyles(primaryColor) {
    if (document.getElementById('lj-claw-styles')) return
    
    const style = document.createElement('style')
    style.id = 'lj-claw-styles'
    style.textContent = `
      .lj-claw-widget {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        position: fixed;
        z-index: 999999;
        bottom: ${config.offsetY}px;
        ${config.position === 'bottom-left' ? 'left' : 'right'}: ${config.offsetX}px;
      }

      .lj-claw-toggle {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        border: none;
        background: ${primaryColor};
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
      }

      .lj-claw-toggle:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0,0,0,0.25);
      }

      .lj-claw-badge {
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

      .lj-claw-window {
        position: absolute;
        bottom: 70px;
        ${config.position === 'bottom-left' ? 'left' : 'right'}: 0;
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
        animation: lj-claw-fadeIn 0.2s ease;
      }

      @keyframes lj-claw-fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }

      .lj-claw-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 16px;
        background: ${primaryColor};
        color: white;
      }

      .lj-claw-header-info {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .lj-claw-avatar {
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

      .lj-claw-header-text {
        display: flex;
        flex-direction: column;
      }

      .lj-claw-bot-name {
        font-size: 15px;
        font-weight: 600;
      }

      .lj-claw-status {
        font-size: 11px;
        opacity: 0.85;
      }

      .lj-claw-minimize {
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

      .lj-claw-minimize:hover {
        background: rgba(255,255,255,0.15);
      }

      .lj-claw-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .lj-claw-welcome {
        text-align: center;
        color: #6c6a64;
        padding: 24px 16px;
        font-size: 14px;
        line-height: 1.5;
      }

      .lj-claw-msg {
        display: flex;
        flex-direction: column;
        max-width: 80%;
      }

      .lj-claw-msg.user {
        align-self: flex-end;
        align-items: flex-end;
      }

      .lj-claw-msg.assistant {
        align-self: flex-start;
        align-items: flex-start;
      }

      .lj-claw-bubble {
        padding: 10px 14px;
        border-radius: 12px;
        font-size: 14px;
        line-height: 1.5;
        word-wrap: break-word;
      }

      .lj-claw-msg.user .lj-claw-bubble {
        background: ${primaryColor};
        color: white;
        border-bottom-right-radius: 4px;
      }

      .lj-claw-msg.assistant .lj-claw-bubble {
        background: white;
        color: #141413;
        border-bottom-left-radius: 4px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
      }

      .lj-claw-bubble p { margin: 4px 0; }
      .lj-claw-bubble p:first-child { margin-top: 0; }
      .lj-claw-bubble p:last-child { margin-bottom: 0; }
      .lj-claw-bubble code {
        background: #181715;
        color: #faf9f5;
        padding: 1px 5px;
        border-radius: 3px;
        font-size: 12px;
      }
      .lj-claw-bubble pre {
        background: #181715;
        padding: 8px;
        border-radius: 6px;
        overflow-x: auto;
        margin: 6px 0;
      }
      .lj-claw-bubble pre code {
        background: none;
        padding: 0;
      }

      .lj-claw-typing {
        display: flex;
        gap: 4px;
        padding: 12px 16px;
      }

      .lj-claw-typing span {
        width: 8px;
        height: 8px;
        background: #6c6a64;
        border-radius: 50%;
        animation: lj-claw-typing 1.4s infinite;
      }

      .lj-claw-typing span:nth-child(2) { animation-delay: 0.2s; }
      .lj-claw-typing span:nth-child(3) { animation-delay: 0.4s; }

      @keyframes lj-claw-typing {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
        30% { transform: translateY(-4px); opacity: 1; }
      }

      .lj-claw-input-area {
        display: flex;
        gap: 8px;
        padding: 12px 14px;
        border-top: 1px solid #e6dfd8;
        background: white;
      }

      .lj-claw-input {
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

      .lj-claw-input:focus {
        border-color: ${primaryColor};
      }

      .lj-claw-input::placeholder { color: #8e8b82; }
      .lj-claw-input:disabled { opacity: 0.6; }

      .lj-claw-send {
        width: 40px;
        height: 40px;
        border: none;
        border-radius: 50%;
        background: ${primaryColor};
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.15s, opacity 0.15s;
        flex-shrink: 0;
      }

      .lj-claw-send:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .lj-claw-send:not(:disabled):hover {
        transform: scale(1.05);
      }

      @media (max-width: 480px) {
        .lj-claw-window {
          width: calc(100vw - 24px);
          height: calc(100vh - 80px);
          max-height: 600px;
          bottom: 60px;
        }
      }
    `
    document.head.appendChild(style)
  }

  // Simple markdown parser
  function parseMarkdown(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>')
  }

  // Widget class
  class LjClawWidget {
    constructor() {
      this.config = null
      this.messages = []
      this.isOpen = false
      this.loading = false
      this.unread = 0
    }

    init(opts) {
      if (this.initialized) {
        console.warn('[lj_claw] Widget already initialized')
        return
      }

      this.config = getConfig(opts)
      window[CONFIG_KEY] = this.config
      window[INSTANCE_KEY] = this

      // Wait for DOM
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this._mount())
      } else {
        this._mount()
      }

      this.initialized = true
    }

    _mount() {
      injectStyles(this.config.primaryColor)

      const container = document.createElement('div')
      container.id = 'lj-claw-container'
      container.innerHTML = createWidgetHTML(this.config)
      document.body.appendChild(container)

      this._bindEvents()
    }

    _bindEvents() {
      const toggle = document.getElementById('lj-claw-toggle')
      const window = document.getElementById('lj-claw-window')
      const minimize = document.getElementById('lj-claw-minimize')
      const input = document.getElementById('lj-claw-input')
      const sendBtn = document.getElementById('lj-claw-send')

      toggle.addEventListener('click', () => this._toggle())
      minimize.addEventListener('click', () => this._close())
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') this._send()
      })
      sendBtn.addEventListener('click', () => this._send())
    }

    _toggle() {
      const window = document.getElementById('lj-claw-window')
      this.isOpen = !this.isOpen
      window.style.display = this.isOpen ? 'flex' : 'none'
      
      if (this.isOpen) {
        this.unread = 0
        this._updateBadge()
        document.getElementById('lj-claw-input').focus()
      }
    }

    _close() {
      const window = document.getElementById('lj-claw-window')
      this.isOpen = false
      window.style.display = 'none'
    }

    async _send() {
      const input = document.getElementById('lj-claw-input')
      const text = input.value.trim()
      if (!text || this.loading) return

      input.value = ''
      this._addMessage('user', text)
      this._setLoading(true)

      try {
        const res = await fetch(this.config.apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        })

        if (!res.ok) throw new Error('Request failed')

        const reader = res.body?.getReader()
        if (!reader) throw new Error('No response body')

        const decoder = new TextDecoder()
        let assistantMessage = ''

        this._addMessage('assistant', '')
        const msgEl = this._getLastMessageEl()

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
                  if (msgEl) msgEl.innerHTML = this._renderMarkdown(assistantMessage)
                }
              } catch {}
            }
          }
        }

        if (!assistantMessage) {
          if (msgEl) msgEl.textContent = '抱歉，暂时无法回复，请稍后再试。'
        }
      } catch (e) {
        console.error('[lj_claw] Send error:', e)
        this._addMessage('assistant', '抱歉，服务出现问题，请稍后再试。')
      } finally {
        this._setLoading(false)
      }
    }

    _addMessage(role, content) {
      const messagesEl = document.getElementById('lj-claw-messages')
      const msg = document.createElement('div')
      msg.className = `lj-claw-msg ${role}`
      
      if (role === 'assistant' && this.loading) {
        msg.innerHTML = '<div class="lj-claw-bubble lj-claw-typing"><span></span><span></span><span></span></div>'
      } else {
        msg.innerHTML = `<div class="lj-claw-bubble">${this._renderMarkdown(content)}</div>`
      }

      messagesEl.appendChild(msg)
      messagesEl.scrollTop = messagesEl.scrollHeight
    }

    _getLastMessageEl() {
      const messages = document.querySelectorAll('#lj-claw-messages .lj-claw-msg.assistant')
      return messages[messages.length - 1]?.querySelector('.lj-claw-bubble')
    }

    _renderMarkdown(text) {
      return parseMarkdown(text)
    }

    _setLoading(loading) {
      this.loading = loading
      const input = document.getElementById('lj-claw-input')
      const sendBtn = document.getElementById('lj-claw-send')
      input.disabled = loading
      sendBtn.disabled = loading
    }

    _updateBadge() {
      const badge = document.getElementById('lj-claw-badge')
      if (this.unread > 0) {
        badge.textContent = this.unread > 9 ? '9+' : this.unread
        badge.style.display = 'flex'
      } else {
        badge.style.display = 'none'
      }
    }
  }

  // Export
  window.LjClawWidget = new LjClawWidget()
  window.LjClawWidget.initialized = false

})()