<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const devicesList = ref([])
const isScanning = ref(false)
const appiumPorts = ref([
  { port: 4723, role: '主叫发送端 (Device 1)', running: false, log: 'Ready' },
  { port: 4724, role: '被叫接收端 (Device 2)', running: false, log: 'Ready' }
])

async function scanDevices() {
  isScanning.value = true
  try {
    const res = await fetch('/api/detect_udid', { method: 'POST' })
    const data = await res.json()
    if (data.devices) {
      devicesList.value = data.devices.map((d, index) => {
        const parts = d.split(' ')
        return {
          id: parts[0],
          name: parts.slice(1).join(' ') || `Android Device #${index + 1}`,
          type: 'Android (UIAutomator2)',
          status: 'online',
          port: index === 0 ? 4723 : 4724,
          battery: '88%',
          resolution: '1080x2400'
        }
      })
      ElMessage.success(`扫描完成，当前在线接入 ${devicesList.value.length} 台设备`)
    }
  } catch (e) {
    ElMessage.error('扫描设备失败: ' + e.message)
  } finally {
    isScanning.value = false
  }
}

async function checkAppiumStatus() {
  for (const item of appiumPorts.value) {
    try {
      const res = await fetch('/api/detect_appium', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ port: item.port })
      })
      const data = await res.json()
      item.running = !!data.appium
      item.log = item.running ? `在线监听: ${data.appium}` : '未运行'
    } catch {
      item.running = false
      item.log = '探测超时'
    }
  }
}

async function startAppium(port) {
  try {
    const res = await fetch('/api/start_appium', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ os: 'windows', port: port })
    })
    const data = await res.json()
    if (data.success) {
      ElMessage.success(`Appium :${port} 服务已触发启动指令`)
      setTimeout(checkAppiumStatus, 2000)
    }
  } catch (e) {
    ElMessage.error(`启动 Appium :${port} 失败: ${e.message}`)
  }
}

onMounted(() => {
  scanDevices()
  checkAppiumStatus()
})
</script>

<template>
  <div class="devices-platform-container">
    <div class="header-card">
      <div class="card-title">
        <el-icon :size="20" style="color: #7c3aed;"><Cpu /></el-icon>
        <span>移动端自动化设备矩阵与环境中心</span>
      </div>
      <p class="card-desc">集中管理 Android / iOS / 鸿蒙物理设备池，监控 Appium 服务拓扑，提供双机联调映射与自愈能力</p>
    </div>

    <!-- Appium 服务状态条 -->
    <div class="appium-grid">
      <div v-for="appium in appiumPorts" :key="appium.port" class="appium-card">
        <div class="appium-header">
          <span class="appium-title">Appium Server :{{ appium.port }}</span>
          <el-tag size="small" :type="appium.running ? 'success' : 'danger'">
            {{ appium.running ? '运行中 (Active)' : '已离线 (Stopped)' }}
          </el-tag>
        </div>
        <div class="appium-role">{{ appium.role }}</div>
        <div class="appium-log">{{ appium.log }}</div>
        <div class="appium-actions">
          <el-button size="small" type="primary" :disabled="appium.running" @click="startAppium(appium.port)">
            一键拉起服务
          </el-button>
          <el-button size="small" plain @click="checkAppiumStatus">探测连通性</el-button>
        </div>
      </div>
    </div>

    <!-- 设备池大卡片 -->
    <div class="devices-section">
      <div class="section-header">
        <h4>📱 在线测试设备池 ({{ devicesList.length }} 台)</h4>
        <el-button type="primary" size="small" :loading="isScanning" @click="scanDevices">
          重新扫描 USB 设备
        </el-button>
      </div>

      <div v-if="devicesList.length > 0" class="devices-cards">
        <div v-for="(dev, idx) in devicesList" :key="dev.id" class="device-card">
          <div class="dev-top">
            <div class="dev-avatar">
              <el-icon :size="24"><Cellphone /></el-icon>
            </div>
            <div class="dev-meta">
              <div class="dev-name">{{ dev.name }}</div>
              <div class="dev-id">UDID: {{ dev.id }}</div>
            </div>
            <el-tag size="small" type="success">就绪</el-tag>
          </div>

          <div class="dev-specs">
            <div class="spec-row">
              <span class="spec-label">驱动系统:</span>
              <span class="spec-val">{{ dev.type }}</span>
            </div>
            <div class="spec-row">
              <span class="spec-label">绑定端口:</span>
              <span class="spec-val">http://127.0.0.1:{{ dev.port }}</span>
            </div>
            <div class="spec-row">
              <span class="spec-label">分辨率:</span>
              <span class="spec-val">{{ dev.resolution }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <el-icon :size="48" style="color: #cbd5e1;"><Cellphone /></el-icon>
        <p>暂未检测到已连接的手机设备，请确保已开启 USB 调试并连通数据线</p>
        <el-button size="small" type="primary" @click="scanDevices">立即检测</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.devices-platform-container {
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

.appium-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.appium-card {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.appium-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.appium-title {
  font-weight: 700;
  font-size: 14px;
  color: #0f172a;
}

.appium-role {
  font-size: 12px;
  color: #64748b;
  margin: 4px 0;
}

.appium-log {
  font-size: 11px;
  font-family: var(--font-mono);
  color: #3b82f6;
  margin-bottom: 12px;
}

.appium-actions {
  display: flex;
  gap: 10px;
}

.devices-section {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  font-size: 14px;
  color: #1e293b;
}

.devices-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.device-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 10px;
  padding: 16px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  transition: all 0.2s ease;
}

.device-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
  border-color: rgba(37, 99, 235, 0.2);
}

.dev-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.dev-avatar {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2563eb;
}

.dev-meta {
  flex: 1;
}

.dev-name {
  font-weight: 600;
  font-size: 13px;
  color: #0f172a;
}

.dev-id {
  font-size: 11px;
  color: #64748b;
  font-family: var(--font-mono);
  margin-top: 2px;
}

.dev-specs {
  border-top: 1px solid rgba(15, 23, 42, 0.05);
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.spec-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.spec-label {
  color: #64748b;
}

.spec-val {
  color: #0f172a;
  font-weight: 500;
  font-family: var(--font-mono);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #64748b;
  gap: 12px;
}
</style>
