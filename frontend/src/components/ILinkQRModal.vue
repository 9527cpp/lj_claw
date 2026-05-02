<template>
  <div class="ilink-qr-modal" v-if="visible" @click.self="close">
    <div class="qr-dialog">
      <div class="qr-header">
        <h3>微信扫码登录 ClawBot</h3>
        <button class="close-btn" @click="close">×</button>
      </div>

      <div class="qr-body">
        <!-- No QR in progress -->
        <div v-if="qrStatus === 'no_qr' && !loading" class="qr-start">
          <p>点击下方按钮获取二维码，然后用微信扫码登录</p>
          <button class="scan-btn" @click="startQR" :disabled="loading">
            获取二维码
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loading && qrStatus !== 'confirmed'" class="qr-loading">
          <div class="spinner"></div>
          <p>正在生成二维码...</p>
        </div>

        <!-- QR Code displayed -->
        <div v-if="loginUrl && qrStatus === 'pending'" class="qr-display">
          <div class="qr-image-wrapper">
            <img v-if="qrImageUrl" :src="qrImageUrl" alt="QR Code" class="qr-image" />
            <div v-else class="qr-placeholder">
              <div class="qr-ascii" v-if="asciiQR">{{ asciiQR }}</div>
              <p v-else>二维码加载中...</p>
            </div>
          </div>
          <p class="qr-hint">请用微信扫描上方二维码</p>
          <p class="qr-status">
            <span class="status-dot"></span>
            等待扫码...
          </p>
          <button class="refresh-btn" @click="startQR" :disabled="loading">
            刷新二维码
          </button>
        </div>

        <!-- Confirmed -->
        <div v-if="qrStatus === 'confirmed'" class="qr-success">
          <div class="success-icon">✓</div>
          <p>登录成功！</p>
          <p class="success-detail">Token 已保存，正在启动 Bridge...</p>
        </div>

        <!-- Expired -->
        <div v-if="qrStatus === 'expired'" class="qr-expired">
          <p>二维码已过期</p>
          <button class="scan-btn" @click="startQR">刷新二维码</button>
        </div>

        <!-- Error -->
        <div v-if="error" class="qr-error">
          <p>{{ error }}</p>
          <button class="scan-btn" @click="startQR">重试</button>
        </div>
      </div>

      <div class="qr-footer">
        <p class="bridge-status">
          Bridge 状态: {{ bridgeRunning ? '运行中' : '未运行' }}
        </p>
        <div class="actions">
          <button v-if="bridgeRunning" class="stop-btn" @click="stopBridge" :disabled="stopping">
            {{ stopping ? '停止中...' : '停止 Bridge' }}
          </button>
          <button v-else class="start-btn" @click="startBridge" :disabled="starting">
            {{ starting ? '启动中...' : '启动 Bridge' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'login-success'): void
}>()

const loading = ref(false)
const starting = ref(false)
const stopping = ref(false)
const error = ref('')
const qrcodeId = ref('')
const loginUrl = ref('')
const qrStatus = ref<'no_qr' | 'pending' | 'confirmed' | 'expired'>('no_qr')
const bridgeRunning = ref(false)
const asciiQR = ref('')
const qrImageUrl = ref('')

let pollTimer: number | null = null

function close() {
  stopPoll()
  emit('close')
}

async function startQR() {
  loading.value = true
  error.value = ''
  qrcodeId.value = ''
  loginUrl.value = ''
  qrStatus.value = 'pending'
  asciiQR.value = ''
  qrImageUrl.value = ''

  try {
    const res = await fetch('/api/ilink/qr/start', { method: 'POST' })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Failed to start QR login')

    qrcodeId.value = data.qrcode_id || ''
    loginUrl.value = data.login_url || ''

    // QR code image via public API (no local library needed)
    if (loginUrl.value) {
      qrImageUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(loginUrl.value)}`
    }

    qrStatus.value = 'pending'
    startPoll()
  } catch (e: any) {
    error.value = e.message || '获取二维码失败'
  } finally {
    loading.value = false
  }
}

function startPoll() {
  stopPoll()
  // Poll every 2 seconds
  pollTimer = window.setInterval(checkStatus, 2000)
}

function stopPoll() {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function checkStatus() {
  try {
    const res = await fetch('/api/ilink/qr/status')
    const data = await res.json()
    if (!res.ok) return

    qrStatus.value = data.status || 'pending'

    if (data.status === 'confirmed') {
      stopPoll()
      emit('login-success')
      setTimeout(() => {
        close()
      }, 1500)
    } else if (data.status === 'expired') {
      stopPoll()
    }
  } catch {
    // Ignore polling errors
  }
}

async function checkBridgeStatus() {
  try {
    const res = await fetch('/api/ilink/status')
    const data = await res.json()
    bridgeRunning.value = data.running || false
  } catch {
    bridgeRunning.value = false
  }
}

async function startBridge() {
  starting.value = true
  try {
    const res = await fetch('/api/ilink/start', { method: 'POST' })
    if (!res.ok) throw new Error('启动失败')
    bridgeRunning.value = true
  } catch (e: any) {
    error.value = e.message || '启动 Bridge 失败'
  } finally {
    starting.value = false
  }
}

async function stopBridge() {
  stopping.value = true
  try {
    const res = await fetch('/api/ilink/stop', { method: 'POST' })
    if (!res.ok) throw new Error('停止失败')
    bridgeRunning.value = false
  } catch (e: any) {
    error.value = e.message || '停止 Bridge 失败'
  } finally {
    stopping.value = false
  }
}

watch(
  () => props.visible,
  (v) => {
    if (v) {
      checkBridgeStatus()
      // Also check if QR is already in progress
      fetchQRState()
    } else {
      stopPoll()
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  stopPoll()
})

async function fetchQRState() {
  try {
    const res = await fetch('/api/ilink/qr')
    const data = await res.json()
    if (data.status && data.status !== 'no_qr') {
      qrStatus.value = data.status
      qrcodeId.value = data.qrcode_id || ''
      loginUrl.value = data.login_url || ''
      if (data.status === 'pending') {
        // Have existing QR, display it
        if (loginUrl.value) {
          qrImageUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(loginUrl.value)}`
        }
        startPoll()
      }
    } else {
      qrStatus.value = 'no_qr'
    }
  } catch {
    // Ignore
  }
}
</script>

<style scoped>
.ilink-qr-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.qr-dialog {
  background: white;
  border-radius: 12px;
  width: 360px;
  max-width: 90vw;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.qr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.qr-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #333;
}

.qr-body {
  padding: 24px 20px;
  min-height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.qr-start {
  text-align: center;
}

.qr-start p {
  color: #666;
  margin-bottom: 16px;
}

.scan-btn {
  padding: 12px 32px;
  background: #07C160;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
}

.scan-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.qr-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #eee;
  border-top-color: #07C160;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.qr-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.qr-image-wrapper {
  background: white;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  margin-bottom: 12px;
}

.qr-image {
  width: 180px;
  height: 180px;
  display: block;
}

.qr-placeholder {
  width: 180px;
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

.qr-ascii {
  font-family: monospace;
  font-size: 10px;
  white-space: pre;
  color: #333;
}

.qr-hint {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.qr-status {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #07C160;
  font-size: 13px;
  margin-bottom: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #07C160;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.refresh-btn {
  padding: 8px 20px;
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.qr-success {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.success-icon {
  width: 60px;
  height: 60px;
  background: #07C160;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  margin-bottom: 16px;
}

.qr-success p {
  font-size: 16px;
  color: #333;
}

.success-detail {
  color: #999 !important;
  font-size: 13px !important;
  margin-top: 8px;
}

.qr-expired {
  text-align: center;
  padding: 20px;
}

.qr-expired p {
  color: #f44336;
  margin-bottom: 12px;
}

.qr-error {
  text-align: center;
  padding: 20px;
}

.qr-error p {
  color: #f44336;
  margin-bottom: 12px;
}

.qr-footer {
  padding: 16px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bridge-status {
  font-size: 13px;
  color: #666;
}

.actions {
  display: flex;
  gap: 8px;
}

.start-btn, .stop-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
}

.start-btn {
  background: #07C160;
  color: white;
}

.stop-btn {
  background: #f44336;
  color: white;
}

.start-btn:disabled, .stop-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>