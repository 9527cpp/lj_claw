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

  var _instance = null

  function getConfig(opts) {
    return Object.assign({
      apiUrl: '',
      botName: 'AI 客服',
      primaryColor: '#cc785c',
      secondaryColor: '#a9583e',
      welcomeMessage: '您好，有什么可以帮您的？',
      inputPlaceholder: '输入消息...',
      position: 'bottom-right',
      offsetX: 20,
      offsetY: 20
    }, opts)
  }

  function createWidgetHTML(cfg) {
    return '<div class="lj-claw-widget ' + cfg.position + '" id="lj-claw-widget">' +
      '<button class="lj-claw-toggle" id="lj-claw-toggle" aria-label="打开客服">' +
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">' +
          '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>' +
        '</svg>' +
        '<span class="lj-claw-badge" id="lj-claw-badge" style="display:none">0</span>' +
      '</button>' +
      '<div class="lj-claw-window" id="lj-claw-window" style="display:none">' +
        '<div class="lj-claw-header" style="background:' + cfg.primaryColor + '">' +
          '<div class="lj-claw-header-info">' +
            '<div class="lj-claw-avatar" style="background:' + cfg.secondaryColor + '">' + (cfg.botName.charAt(0) || 'AI') + '</div>' +
            '<div class="lj-claw-header-text">' +
              '<span class="lj-claw-bot-name">' + cfg.botName + '</span>' +
              '<span class="lj-claw-status">在线 · 随时为您服务</span>' +
            '</div>' +
          '</div>' +
          '<button class="lj-claw-minimize" id="lj-claw-minimize" aria-label="最小化">' +
            '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">' +
              '<line x1="5" y1="12" x2="19" y2="12"></line>' +
            '</svg>' +
          '</button>' +
        '</div>' +
        '<div class="lj-claw-messages" id="lj-claw-messages">' +
          '<div class="lj-claw-welcome"><p>' + cfg.welcomeMessage + '</p></div>' +
        '</div>' +
        '<div class="lj-claw-input-area">' +
          '<input type="text" class="lj-claw-input" id="lj-claw-input" placeholder="' + cfg.inputPlaceholder + '" />' +
          '<button class="lj-claw-send" id="lj-claw-send" style="background:' + cfg.primaryColor + '">' +
            '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">' +
              '<line x1="22" y1="2" x2="11" y2="13"></line>' +
              '<polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>' +
            '</svg>' +
          '</button>' +
        '</div>' +
      '</div>' +
    '</div>'
  }

  function parseMarkdown(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>')
  }

  function LjClawWidget() {
    this.config = null
    this.isOpen = false
    this.loading = false
    this.unread = 0
  }

  LjClawWidget.prototype.init = function (opts) {
    var self = this

    this.config = getConfig(opts)

    if (document.getElementById('lj-claw-widget')) {
      console.warn('[lj_claw] Widget already initialized')
      return
    }

    injectStyles(this.config)

    var container = document.createElement('div')
    container.id = 'lj-claw-container'
    container.innerHTML = createWidgetHTML(this.config)
    document.body.appendChild(container)

    this._bindEvents()
  }

  LjClawWidget.prototype._bindEvents = function () {
    var self = this
    var toggle = document.getElementById('lj-claw-toggle')
    var minimize = document.getElementById('lj-claw-minimize')
    var input = document.getElementById('lj-claw-input')
    var sendBtn = document.getElementById('lj-claw-send')

    toggle.addEventListener('click', function () {
      self._toggle()
    })

    minimize.addEventListener('click', function () {
      self._close()
    })

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') self._send()
    })

    sendBtn.addEventListener('click', function () {
      self._send()
    })
  }

  LjClawWidget.prototype._toggle = function () {
    var win = document.getElementById('lj-claw-window')
    this.isOpen = !this.isOpen
    win.style.display = this.isOpen ? 'flex' : 'none'

    if (this.isOpen) {
      this.unread = 0
      this._updateBadge()
      document.getElementById('lj-claw-input').focus()
    }
  }

  LjClawWidget.prototype._close = function () {
    var win = document.getElementById('lj-claw-window')
    this.isOpen = false
    win.style.display = 'none'
  }

  LjClawWidget.prototype._send = function () {
    var self = this
    var input = document.getElementById('lj-claw-input')
    var sendBtn = document.getElementById('lj-claw-send')
    var text = input.value.trim()

    if (!text || this.loading) return

    input.value = ''
    this._addMessage('user', text)
    this._setLoading(true)

    fetch(this.config.apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    }).then(function (res) {
      if (!res.ok) throw new Error('Request failed')
      return res.body.getReader()
    }).then(function (reader) {
      if (!reader) throw new Error('No response body')
      var decoder = new TextDecoder()
      var assistantMessage = ''

      self._addMessage('assistant', '')
      var msgEl = self._getLastMessageEl()

      function read() {
        reader.read().then(function (result) {
          if (result.done) return

          var chunk = decoder.decode(result.value)
          var lines = chunk.split('\n')

          for (var i = 0; i < lines.length; i++) {
            var line = lines[i]
            if (line.indexOf('data: ') === 0) {
              try {
                var data = JSON.parse(line.substring(6))
                if (data.type === 'text') {
                  assistantMessage += data.content
                  if (msgEl) msgEl.innerHTML = parseMarkdown(assistantMessage)
                }
              } catch (e) {}
            }
          }

          read()
        })
      }

      read()
    }).catch(function (e) {
      console.error('[lj_claw] Send error:', e)
      self._addMessage('assistant', '抱歉，服务出现问题，请稍后再试。')
    }).finally(function () {
      self._setLoading(false)
    })
  }

  LjClawWidget.prototype._addMessage = function (role, content) {
    var messagesEl = document.getElementById('lj-claw-messages')
    var msg = document.createElement('div')
    msg.className = 'lj-claw-msg ' + role

    if (role === 'assistant' && this.loading) {
      msg.innerHTML = '<div class="lj-claw-bubble lj-claw-typing"><span></span><span></span><span></span></div>'
    } else {
      msg.innerHTML = '<div class="lj-claw-bubble">' + parseMarkdown(content) + '</div>'
    }

    messagesEl.appendChild(msg)
    messagesEl.scrollTop = messagesEl.scrollHeight
  }

  LjClawWidget.prototype._getLastMessageEl = function () {
    var msgs = document.querySelectorAll('#lj-claw-messages .lj-claw-msg.assistant')
    var last = msgs[msgs.length - 1]
    return last ? last.querySelector('.lj-claw-bubble') : null
  }

  LjClawWidget.prototype._setLoading = function (loading) {
    this.loading = loading
    var input = document.getElementById('lj-claw-input')
    var sendBtn = document.getElementById('lj-claw-send')
    input.disabled = loading
    sendBtn.disabled = loading
  }

  LjClawWidget.prototype._updateBadge = function () {
    var badge = document.getElementById('lj-claw-badge')
    if (this.unread > 0) {
      badge.textContent = this.unread > 9 ? '9+' : this.unread
      badge.style.display = 'flex'
    } else {
      badge.style.display = 'none'
    }
  }

  // ── Styles ──────────────────────────────────────────────────────────────────
  function injectStyles(cfg) {
    if (document.getElementById('lj-claw-styles')) return

    var style = document.createElement('style')
    style.id = 'lj-claw-styles'
    style.textContent = [
      '.lj-claw-widget{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;position:fixed;z-index:999999;bottom:' + cfg.offsetY + 'px;' + (cfg.position === 'bottom-left' ? 'left' : 'right') + ':' + cfg.offsetX + 'px}',
      '.lj-claw-toggle{width:56px;height:56px;border-radius:50%;border:none;background:' + cfg.primaryColor + ';cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(0,0,0,0.2);transition:transform .2s,box-shadow .2s;position:relative}',
      '.lj-claw-toggle:hover{transform:scale(1.05);box-shadow:0 6px 20px rgba(0,0,0,0.25)}',
      '.lj-claw-badge{position:absolute;top:-2px;right:-2px;background:#c64545;color:white;font-size:11px;font-weight:600;min-width:18px;height:18px;border-radius:9px;display:flex;align-items:center;justify-content:center;padding:0 4px}',
      '.lj-claw-window{position:absolute;bottom:70px;' + (cfg.position === 'bottom-left' ? 'left' : 'right') + ':0;width:360px;height:520px;max-height:80vh;background:#faf9f5;border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;overflow:hidden;border:1px solid #e6dfd8;animation:ljIn .2s ease}',
      '@keyframes ljIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}',
      '.lj-claw-header{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;color:white}',
      '.lj-claw-header-info{display:flex;align-items:center;gap:10px}',
      '.lj-claw-avatar{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:600;color:white}',
      '.lj-claw-header-text{display:flex;flex-direction:column}',
      '.lj-claw-bot-name{font-size:15px;font-weight:600}',
      '.lj-claw-status{font-size:11px;opacity:.85}',
      '.lj-claw-minimize{background:none;border:none;cursor:pointer;padding:6px;border-radius:6px;display:flex;align-items:center;justify-content:center;transition:background .2s}',
      '.lj-claw-minimize:hover{background:rgba(255,255,255,.15)}',
      '.lj-claw-messages{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px}',
      '.lj-claw-welcome{text-align:center;color:#6c6a64;padding:24px 16px;font-size:14px;line-height:1.5}',
      '.lj-claw-msg{display:flex;flex-direction:column;max-width:80%}',
      '.lj-claw-msg.user{align-self:flex-end;align-items:flex-end}',
      '.lj-claw-msg.assistant{align-self:flex-start;align-items:flex-start}',
      '.lj-claw-bubble{padding:10px 14px;border-radius:12px;font-size:14px;line-height:1.5;word-wrap:break-word}',
      '.lj-claw-msg.user .lj-claw-bubble{background:' + cfg.primaryColor + ';color:white;border-bottom-right-radius:4px}',
      '.lj-claw-msg.assistant .lj-claw-bubble{background:white;color:#141413;border-bottom-left-radius:4px;box-shadow:0 1px 4px rgba(0,0,0,.06)}',
      '.lj-claw-bubble p{margin:4px 0}',
      '.lj-claw-bubble p:first-child{margin-top:0}',
      '.lj-claw-bubble p:last-child{margin-bottom:0}',
      '.lj-claw-bubble code{background:#181715;color:#faf9f5;padding:1px 5px;border-radius:3px;font-size:12px}',
      '.lj-claw-bubble pre{background:#181715;padding:8px;border-radius:6px;overflow-x:auto;margin:6px 0}',
      '.lj-claw-bubble pre code{background:none;padding:0}',
      '.lj-claw-typing{display:flex;gap:4px;padding:12px 16px}',
      '.lj-claw-typing span{width:8px;height:8px;background:#6c6a64;border-radius:50%;animation:ljDot 1.4s infinite}',
      '.lj-claw-typing span:nth-child(2){animation-delay:.2s}',
      '.lj-claw-typing span:nth-child(3){animation-delay:.4s}',
      '@keyframes ljDot{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-4px);opacity:1}}',
      '.lj-claw-input-area{display:flex;gap:8px;padding:12px 14px;border-top:1px solid #e6dfd8;background:white}',
      '.lj-claw-input{flex:1;border:1px solid #e6dfd8;border-radius:20px;padding:10px 16px;font-size:14px;outline:none;color:#141413;background:#faf9f5;transition:border-color .2s}',
      '.lj-claw-input:focus{border-color:' + cfg.primaryColor + '}',
      ".lj-claw-input::placeholder{color:#8e8b82}",
      '.lj-claw-input:disabled{opacity:.6}',
      '.lj-claw-send{width:40px;height:40px;border:none;border-radius:50%;background:' + cfg.primaryColor + ';cursor:pointer;display:flex;align-items:center;justify-content:center;transition:transform .15s,opacity .15s;flex-shrink:0}',
      '.lj-claw-send:disabled{opacity:.4;cursor:not-allowed}',
      '.lj-claw-send:not(:disabled):hover{transform:scale(1.05)}',
      '@media(max-width:480px){.lj-claw-window{width:calc(100vw - 24px);height:calc(100vh - 80px);max-height:600px;bottom:60px}}'
    ].join('')

    document.head.appendChild(style)
  }

  // ── Export ──────────────────────────────────────────────────────────────────
  _instance = new LjClawWidget()
  window.LjClawWidget = _instance

})()
