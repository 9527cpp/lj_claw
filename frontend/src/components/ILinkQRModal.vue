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
  background: rgba(20, 20, 19, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(3px);
}

.qr-dialog {
  background: #faf9f5;
  border-radius: 14px;
  width: 380px;
  max-width: 90vw;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  border: 1px solid #e6dfd8;
}

.qr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid #e6dfd8;
  background: white;
}

.qr-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #141413;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 26px;
  color: #8e8b82;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #3d3d3a;
}

.qr-body {
  padding: 28px 24px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #faf9f5;
}

.qr-start {
  text-align: center;
  padding: 20px 0;
}

.qr-start p {
  color: #6c6a64;
  font-size: 14px;
  margin-bottom: 20px;
  line-height: 1.5;
}

.scan-btn {
  padding: 12px 36px;
  background: #07C160;
  color: white;
  border: none;
  border-radius: 7px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.scan-btn:hover { background: #06a050; }
.scan-btn:disabled {
  background: #e6dfd8;
  color: #8e8b82;
  cursor: not-allowed;
}

.qr-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
}

.spinner {
  width: 42px;
  height: 42px;
  border: 3px solid #ebe6df;
  border-top-color: #07C160;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 18px;
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
  padding: 14px;
  border: 1px solid #e6dfd8;
  border-radius: 10px;
  margin-bottom: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
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
  color: #8e8b82;
}

.qr-ascii {
  font-family: 'SF Mono', 'Monaco', monospace;
  font-size: 9px;
  white-space: pre;
  color: #3d3d3a;
}

.qr-hint {
  color: #6c6a64;
  font-size: 13px;
  margin-bottom: 8px;
}

.qr-status {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #07C160;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 14px;
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
  background: #f5f0e8;
  color: #6c6a64;
  border: 1px solid #e6dfd8;
  border-radius: 5px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.refresh-btn:hover {
  background: #e8e0d2;
  color: #3d3d3a;
}
.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.qr-success {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
}

.success-icon {
  width: 64px;
  height: 64px;
  background: #5db8a6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  margin-bottom: 18px;
}

.qr-success p {
  font-size: 16px;
  font-weight: 500;
  color: #141413;
}

.success-detail {
  color: #6c6a64 !important;
  font-size: 13px !important;
  margin-top: 8px;
  font-weight: 400 !important;
}

.qr-expired {
  text-align: center;
  padding: 24px;
}

.qr-expired p {
  color: #c64545;
  font-size: 14px;
  margin-bottom: 14px;
}

.qr-error {
  text-align: center;
  padding: 24px;
}

.qr-error p {
  color: #c64545;
  font-size: 14px;
  margin-bottom: 14px;
}

.qr-footer {
  padding: 16px 24px;
  border-top: 1px solid #e6dfd8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
}

.bridge-status {
  font-size: 13px;
  color: #6c6a64;
}

.actions {
  display: flex;
  gap: 8px;
}

.start-btn, .stop-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.start-btn {
  background: #07C160;
  color: white;
}
.start-btn:hover { background: #06a050; }

.stop-btn {
  background: #c64545;
  color: white;
}
.stop-btn:hover { background: #a33a3a; }

.start-btn:disabled, .stop-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>