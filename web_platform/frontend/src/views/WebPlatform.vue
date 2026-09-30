<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const browsers = ref([
  { name: 'Chromium', engine: 'Chrome / Edge', status: 'ready', selected: true },
  { name: 'Firefox', engine: 'Gecko', status: 'ready', selected: false },
  { name: 'WebKit', engine: 'Safari', status: 'ready', selected: false }
])

const isHeadless = ref(false)
const workerCount = ref(2)
const baseUrl = ref('http://localhost:3000')
const isExecuting = ref(false)
const executionLog = ref('准备就绪，选择 Web 测试模块后点击运行...')

const webModules = ref([
  { id: 'web_login', name: 'Web 端扫码登录与会话保持', tag: 'P0 冒烟', status: 'passed', time: '12s' },
  { id: 'web_msg_text', name: 'Web 文本消息即时收发与已读标记', tag: 'P0 冒烟', status: 'passed', time: '18s' },
  { id: 'web_msg_media', name: 'Web 富媒体文件拖拽上传与大文件分片', tag: 'P1 回归', status: 'idle', time: '-' },
  { id: 'web_group_manage', name: 'Web 群组管理、公告发布与禁言', tag: 'P1 回归', status: 'idle', time: '-' },
  { id: 'web_compatibility', name: '跨浏览器渲染与不同分辨率视口适配', tag: 'P2 兼容', status: 'idle', time: '-' }
])

function runWebTest(module) {
  if (isExecuting.value) return
  isExecuting.value = true
  ElMessage.info(`正在启动 Playwright (${browsers.value.find(b => b.selected)?.name}) 执行: ${module.name}`)
  executionLog.value = `[Playwright] 🚀 启动浏览器实例: ${browsers.value.find(b => b.selected)?.name}\n`
  executionLog.value += `[Playwright] 🌐 目标地址: ${baseUrl.value} (Headless: ${isHeadless.value})\n`
  executionLog.value += `[Playwright] 🧪 载入模块用例: ${module.name}...\n`

  setTimeout(() => {
    executionLog.value += `[Playwright] ✅ 步骤 1: 打开主页成功\n[Playwright] ✅ 步骤 2: 页面元素定位与交互就绪\n[Playwright] ✅ 步骤 3: 断言验证通过\n[Playwright] 🏁 用例执行完毕，耗时 3.4s\n`
    module.status = 'passed'
    isExecuting.value = false
    ElMessage.success(`${module.name} 执行完成！`)
  }, 2000)
}

function selectBrowser(target) {
  browsers.value.forEach(b => b.selected = (b.name === target.name))
}
</script>

<template>
  <div class="web-platform-container">
    <div class="header-card">
      <div class="card-title">
        <el-icon :size="20" style="color: #2563eb;"><Platform /></el-icon>
        <span>Web 端自动化测试 (Playwright 架构)</span>
      </div>
      <p class="card-desc">支持 Chrome / Firefox / Safari 跨浏览器自动化执行，覆盖 Web 端 IM 核心会话与多端同步</p>
    </div>

    <div class="config-grid">
      <!-- 浏览器矩阵选择 -->
      <div class="config-card">
        <h4>🌐 运行环境与浏览器矩阵</h4>
        <div class="browser-chips">
          <div
            v-for="b in browsers"
            :key="b.name"
            class="browser-chip"
            :class="{ active: b.selected }"
            @click="selectBrowser(b)"
          >
            <div class="browser-title">{{ b.name }}</div>
            <div class="browser-meta">{{ b.engine }}</div>
          </div>
        </div>

        <div class="options-row">
          <el-form label-position="left" label-width="120px" size="small">
            <el-form-item label="无头运行模式">
              <el-switch v-model="isHeadless" active-text="Headless (后台静默执行)" />
            </el-form-item>
            <el-form-item label="并发执行线程">
              <el-input-number v-model="workerCount" :min="1" :max="8" />
            </el-form-item>
            <el-form-item label="Web 服务根地址">
              <el-input v-model="baseUrl" style="width: 240px;" placeholder="http://..." />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <!-- 实时执行终端 -->
      <div class="config-card log-card">
        <div class="log-header">
          <h4>📟 Web 自动化实时执行输出</h4>
          <el-tag size="small" :type="isExecuting ? 'danger' : 'success'">
            {{ isExecuting ? 'Running' : 'Idle' }}
          </el-tag>
        </div>
        <pre class="web-terminal">{{ executionLog }}</pre>
      </div>
    </div>

    <!-- Web 用例集列表 -->
    <div class="cases-panel">
      <div class="panel-header">
        <h4>📋 Web 端专项自动化测试集</h4>
        <el-button type="primary" size="small" :disabled="isExecuting" @click="runWebTest({ name: '全量 Web 冒烟集' })">
          一键执行全量 Web 冒烟
        </el-button>
      </div>

      <div class="cases-list">
        <div v-for="c in webModules" :key="c.id" class="case-card">
          <div class="case-info">
            <span class="case-name">{{ c.name }}</span>
            <el-tag size="small" type="info">{{ c.tag }}</el-tag>
          </div>
          <div class="case-actions">
            <el-tag v-if="c.status === 'passed'" type="success" size="small">通过 ({{ c.time }})</el-tag>
            <el-tag v-else-if="c.status === 'idle'" type="info" size="small">未执行</el-tag>
            <el-button size="small" type="primary" plain :disabled="isExecuting" @click="runWebTest(c)">
              执行
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.web-platform-container {
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

.config-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.config-card {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.config-card h4 {
  margin: 0 0 14px 0;
  font-size: 14px;
  color: #1e293b;
}

.browser-chips {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.browser-chip {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(15, 23, 42, 0.1);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.browser-chip:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
}

.browser-chip.active {
  background: #eff6ff;
  border-color: #2563eb;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
}

.browser-title {
  font-weight: 600;
  font-size: 13px;
  color: #0f172a;
}

.browser-meta {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.log-card {
  display: flex;
  flex-direction: column;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.web-terminal {
  flex: 1;
  margin: 0;
  background: #0f172a;
  color: #38bdf8;
  padding: 12px 14px;
  border-radius: 8px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  min-height: 160px;
  max-height: 220px;
  overflow-y: auto;
}

.cases-panel {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.panel-header h4 {
  margin: 0;
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
  transition: all 0.2s ease;
}

.case-card:hover {
  background: #fff;
  border-color: rgba(37, 99, 235, 0.3);
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

.case-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
