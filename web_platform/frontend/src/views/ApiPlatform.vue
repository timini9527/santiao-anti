<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const wsUrl = ref('ws://127.0.0.1:8080/ws/im')
const token = ref('Bearer test_user_session_token_1001')
const isConnected = ref(false)
const heartbeatSeconds = ref(30)
const concurrentUsers = ref(500)
const spawnRate = ref(20)
const isStressTesting = ref(false)
const stressMetrics = ref({
  currentQps: 0,
  p99Latency: 0,
  packetLoss: '0%',
  totalSent: 0
})

const protocolCases = ref([
  { id: 'proto_handshake', name: 'WebSocket 协议握手与鉴权 Token 绑定', type: '协议鉴权', status: 'passed' },
  { id: 'proto_heartbeat', name: '心跳维持 PING/PONG 超时断线检测', type: '链路维持', status: 'passed' },
  { id: 'proto_seq', name: '消息顺序递增 seq 机制与客户端幂等去重', type: '顺序一致性', status: 'idle' },
  { id: 'proto_offline', name: '离线消息拉取与多端补偿同步 (SyncMsg)', type: '离线补偿', status: 'idle' },
  { id: 'proto_locust', name: '单群 1000 人同时在线抢红包与刷屏高并发', type: '高并发性能', status: 'idle' }
])

let stressTimer = null

function toggleWsConnection() {
  if (isConnected.value) {
    isConnected.value = false
    ElMessage.info('WebSocket 长连接已断开')
  } else {
    isConnected.value = true
    ElMessage.success('WebSocket 长连接建立握手成功！')
  }
}

function startStressTest() {
  if (isStressTesting.value) {
    isStressTesting.value = false
    clearInterval(stressTimer)
    ElMessage.info('性能压测已停止')
    return
  }

  isStressTesting.value = true
  ElMessage.warning(`正在启动 Locust 模拟 ${concurrentUsers.value} 并发长连接压测...`)

  stressTimer = setInterval(() => {
    stressMetrics.value.currentQps = Math.floor(800 + Math.random() * 400)
    stressMetrics.value.p99Latency = Math.floor(120 + Math.random() * 60)
    stressMetrics.value.totalSent += Math.floor(150 + Math.random() * 50)
  }, 1000)
}
</script>

<template>
  <div class="api-platform-container">
    <div class="header-card">
      <div class="card-title">
        <el-icon :size="20" style="color: #059669;"><Connection /></el-icon>
        <span>IM 即时通讯接口与长连接性能测试平台</span>
      </div>
      <p class="card-desc">针对 WebSocket 长连接协议、Protobuf/gRPC 接口、离线消息补偿及 Locust 高并发收发压力测试</p>
    </div>

    <!-- 性能与长连接状态大盘 -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">WebSocket 链路状态</div>
        <div class="metric-value" :class="isConnected ? 'text-success' : 'text-muted'">
          {{ isConnected ? '🟢 Connected' : '⚪ Disconnected' }}
        </div>
        <div class="metric-sub">心跳间隔: {{ heartbeatSeconds }}s</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">压测当前 QPS (吞吐量)</div>
        <div class="metric-value text-primary">{{ stressMetrics.currentQps }} msg/s</div>
        <div class="metric-sub">并发用户: {{ concurrentUsers }} 个</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">关键路径 P99 响应延迟</div>
        <div class="metric-value text-warning">{{ stressMetrics.p99Latency }} ms</div>
        <div class="metric-sub">门禁基线: &le; 500ms</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">累计消息发送总量</div>
        <div class="metric-value text-indigo">{{ stressMetrics.totalSent }} 条</div>
        <div class="metric-sub">丢包率: 0.00% (正常)</div>
      </div>
    </div>

    <!-- 配置面板 -->
    <div class="config-grid">
      <div class="config-card">
        <h4>⚡ WebSocket 长连接配置</h4>
        <el-form label-position="top" size="small">
          <el-form-item label="WebSocket 地址">
            <el-input v-model="wsUrl" placeholder="ws://..." />
          </el-form-item>
          <el-form-item label="用户鉴权 Token">
            <el-input v-model="token" placeholder="Bearer ..." />
          </el-form-item>
          <el-button :type="isConnected ? 'danger' : 'success'" size="small" @click="toggleWsConnection">
            {{ isConnected ? '断开长连接' : '建立长连接握手' }}
          </el-button>
        </el-form>
      </div>

      <div class="config-card">
        <h4>🚀 Locust 并发消息压力测试</h4>
        <el-form label-position="top" size="small">
          <div style="display: flex; gap: 16px;">
            <el-form-item label="并发长连接用户数" style="flex: 1;">
              <el-input-number v-model="concurrentUsers" :min="10" :max="5000" :step="100" />
            </el-form-item>
            <el-form-item label="每秒生成速率 (Users/s)" style="flex: 1;">
              <el-input-number v-model="spawnRate" :min="1" :max="100" />
            </el-form-item>
          </div>
          <el-button :type="isStressTesting ? 'danger' : 'warning'" size="small" @click="startStressTest">
            {{ isStressTesting ? '停止并发压测' : '启动 1000 并发压力测试' }}
          </el-button>
        </el-form>
      </div>
    </div>

    <!-- 协议用例集 -->
    <div class="cases-panel">
      <h4>📋 IM 专项协议测试套件</h4>
      <div class="cases-list">
        <div v-for="item in protocolCases" :key="item.id" class="case-card">
          <div class="case-info">
            <span class="case-name">{{ item.name }}</span>
            <el-tag size="small" type="success">{{ item.type }}</el-tag>
          </div>
          <el-button size="small" type="primary" plain>执行协议断言</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.api-platform-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  box-sizing: border-box;
}

.header-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  padding: 18px 24px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.card-desc {
  margin: 6px 0 0 0;
  color: #64748b;
  font-size: 13px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.metric-card {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  padding: 16px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.metric-label {
  font-size: 12px;
  color: #64748b;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  margin: 8px 0 4px 0;
  font-family: var(--font-mono);
}

.metric-sub {
  font-size: 11px;
  color: #94a3b8;
}

.text-success { color: #059669; }
.text-primary { color: #2563eb; }
.text-warning { color: #d97706; }
.text-indigo { color: #7c3aed; }
.text-muted { color: #94a3b8; }

.config-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.config-card, .cases-panel {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.config-card h4, .cases-panel h4 {
  margin: 0 0 14px 0;
  font-size: 14px;
  color: #1e293b;
}

.cases-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.case-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 8px;
  border: 1px solid rgba(15, 23, 42, 0.05);
}

.case-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.case-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
}
</style>
