<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh, Cellphone, Platform, Connection, Cpu, DataAnalysis } from '@element-plus/icons-vue'

// 引入 5 大业务平台视图组件
import MobilePlatform from './views/MobilePlatform.vue'
import WebPlatform from './views/WebPlatform.vue'
import ApiPlatform from './views/ApiPlatform.vue'
import DevicesPlatform from './views/DevicesPlatform.vue'
import ReportsPlatform from './views/ReportsPlatform.vue'

// ==================== 1. 多平台导航定义 ====================
const activePlatform = ref('mobile')

const platformList = [
  { key: 'mobile', name: '移动 IM', icon: Cellphone, tag: 'Core', desc: 'Appium 移动端自动化测试' },
  { key: 'web', name: 'Web 测试', icon: Platform, tag: 'UI', desc: 'Playwright Web UI 自动化兼容性测试' },
  { key: 'api', name: '接口压测', icon: Connection, tag: 'IM', desc: 'WebSocket 协议通信与 Locust 并发压力测试' },
  { key: 'devices', name: '设备矩阵', icon: Cpu, tag: 'Grid', desc: '多设备矩阵与 Appium 服务实时监控' },
  { key: 'reports', name: '报告中心', icon: DataAnalysis, tag: 'Allure', desc: '全量历史测试报告与质量门禁看板' }
]

// ==================== 2. 全局状态概览 ====================
const overviewData = ref({
  total_cases: 0,
  connected_devices: 0,
  device_list: [],
  history_reports: 0,
  appium_port_4723: false,
  appium_port_4724: false
})

async function fetchOverview() {
  try {
    const res = await fetch('/api/overview')
    const data = await res.json()
    if (data.success) {
      overviewData.value = data
    }
  } catch (e) {
    console.error('获取概览统计失败:', e)
  }
}

function refreshAllPlatforms() {
  fetchOverview()
}

onMounted(() => {
  fetchOverview()
})

const currentPlatformMeta = computed(() => {
  return platformList.find(p => p.key === activePlatform.value) || platformList[0]
})
</script>

<template>
  <div class="shell-layout">
    <!-- 1. 全球科技级主侧边栏导航 (Global Platform Navigator) -->
    <aside class="global-nav-rail">
      <div class="rail-brand">
        <div class="brand-badge">ST</div>
        <span class="brand-text">SANTIAO</span>
      </div>

      <nav class="rail-menu">
        <div
          v-for="item in platformList"
          :key="item.key"
          class="rail-item"
          :class="{ active: activePlatform === item.key }"
          @click="activePlatform = item.key"
        >
          <div class="rail-icon">
            <el-icon :size="20"><component :is="item.icon" /></el-icon>
          </div>
          <span class="rail-label">{{ item.name }}</span>
          <span v-if="item.tag" class="rail-tag" :class="item.tag.toLowerCase()">{{ item.tag }}</span>
        </div>
      </nav>

      <div class="rail-footer">
        <el-tooltip content="FastAPI 后端运行在 8000 端口" placement="right">
          <div class="server-status-pill">
            <span class="pulse-dot"></span>
            <span class="port-label">8000</span>
          </div>
        </el-tooltip>
      </div>
    </aside>

    <!-- 2. 主操作工作区 (Main Workspace) -->
    <div class="platform-workspace">
      <!-- 平台统一顶部标题与快速状态栏 -->
      <header class="workspace-header">
        <div class="workspace-title-group">
          <div class="platform-indicator-icon">
            <el-icon :size="18"><component :is="currentPlatformMeta.icon" /></el-icon>
          </div>
          <div>
            <h2 class="workspace-title">
              {{ currentPlatformMeta.name }} 控制台
            </h2>
            <p class="workspace-subtitle">
              {{ currentPlatformMeta.desc }}
            </p>
          </div>
        </div>

        <div class="workspace-header-actions">
          <div class="stat-pill">
            <span class="stat-dot" :class="overviewData.connected_devices > 0 ? 'online' : 'offline'"></span>
            <span>设备: <strong>{{ overviewData.connected_devices }}</strong> 台在线</span>
          </div>
          <el-tooltip :content="`当前测试工程共计 ${overviewData.total_cases} 条可执行用例 (含 ${overviewData.total_functions || 376} 个测试函数及参数化展开实例)`" placement="bottom">
            <div class="stat-pill" style="cursor: pointer;">
              <span class="stat-icon">🧪</span>
              <span>用例: <strong>{{ overviewData.total_cases }}</strong> 条</span>
            </div>
          </el-tooltip>
          <div class="stat-pill">
            <span class="stat-icon">📑</span>
            <span>报告: <strong>{{ overviewData.history_reports }}</strong> 份</span>
          </div>
          <el-button size="small" :icon="Refresh" circle @click="refreshAllPlatforms" title="刷新平台状态" />
        </div>
      </header>

      <!-- 平台主体工作视图：使用 v-show 保持正在运行的组件状态与日志不被卸载 -->
      <div class="workspace-content">
        <MobilePlatform v-show="activePlatform === 'mobile'" />
        <WebPlatform v-show="activePlatform === 'web'" />
        <ApiPlatform v-show="activePlatform === 'api'" />
        <DevicesPlatform v-show="activePlatform === 'devices'" />
        <ReportsPlatform v-show="activePlatform === 'reports'" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.shell-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: var(--bg-main);
}

/* ==================== 1. 最左侧全局导航 Rail ==================== */
.global-nav-rail {
  width: 76px;
  background: #0f172a; /* 睿智深邃曜石黑蓝底色 */
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  box-shadow: 4px 0 24px rgba(15, 23, 42, 0.15);
  z-index: 100;
  flex-shrink: 0;
  user-select: none;
}

.rail-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-bottom: 24px;
}

.brand-badge {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #10b981 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-family: var(--font-mono);
  font-size: 15px;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
}

.brand-text {
  font-size: 9px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 1px;
}

.rail-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  padding: 0 8px;
  box-sizing: border-box;
}

.rail-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px 4px;
  border-radius: 10px;
  color: #94a3b8;
  cursor: pointer;
  position: relative;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.rail-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
  transform: translateY(-1px);
}

.rail-item.active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.35) 0%, rgba(59, 130, 246, 0.2) 100%);
  color: #60a5fa;
  box-shadow: 0 0 15px rgba(37, 99, 235, 0.25);
  border: 1px solid rgba(96, 165, 250, 0.3);
}

.rail-icon {
  margin-bottom: 4px;
}

.rail-label {
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.rail-tag {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 8px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 4px;
  background: #334155;
  color: #94a3b8;
}

.rail-tag.core {
  background: #2563eb;
  color: #fff;
}

.rail-tag.ui {
  background: #0284c7;
  color: #fff;
}

.rail-footer {
  margin-top: auto;
}

.server-status-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.port-label {
  font-size: 10px;
  font-family: var(--font-mono);
  color: #94a3b8;
}

/* ==================== 2. 主操作工作区 ==================== */
.platform-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.workspace-header {
  height: 56px;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(15px);
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  flex-shrink: 0;
}

.workspace-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.platform-indicator-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #eff6ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(37, 99, 235, 0.15);
}

.workspace-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.workspace-subtitle {
  margin: 2px 0 0 0;
  font-size: 11.5px;
  color: #64748b;
}

.workspace-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #475569;
  background: rgba(255, 255, 255, 0.7);
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.stat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.stat-dot.online {
  background: #10b981;
  box-shadow: 0 0 5px rgba(16, 185, 129, 0.8);
}

.stat-dot.offline {
  background: #94a3b8;
}

.stat-icon {
  font-size: 13px;
}

.workspace-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.workspace-content > * {
  height: 100%;
  width: 100%;
}
</style>
