<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'

const historyReports = ref([])
const selectedReport = ref(null)
const currentReportUrl = ref('')
const isLoading = ref(false)

// 质量门禁核心指标（从后端动态获取实时统计）
const metrics = ref({
  coverage_rate: 85.5,
  coverage_target: 80.0,
  coverage_is_passed: true,
  smoke_pass_rate: 100.0,
  smoke_target: 95.0,
  smoke_is_passed: true,
  flaky_rate: 0.0,
  flaky_target: 2.0,
  flaky_is_healthy: true,
  total_cases: 0,
  total_executed: 0,
  total_passed: 0,
  total_failed: 0
})

async function fetchHistoryReports() {
  isLoading.value = true
  try {
    const res = await fetch('/api/reports/history')
    const data = await res.json()
    if (data.metrics) {
      metrics.value = data.metrics
    }
    if (data.success && data.history) {
      historyReports.value = data.history
      if (data.history.length > 0 && !selectedReport.value) {
        selectReport(data.history[0])
      }
    }
  } catch (e) {
    ElMessage.error('加载历史报告列表失败: ' + e.message)
  } finally {
    isLoading.value = false
  }
}

const selectedRole = ref('business')
const iframeRef = ref(null)

function syncReportRole() {
  const role = selectedRole.value
  if (iframeRef.value && iframeRef.value.contentWindow) {
    try {
      iframeRef.value.contentWindow.postMessage(`role:${role}`, '*')
      iframeRef.value.contentWindow.postMessage({ type: 'ALLURE_ROLE_SWITCH', role }, '*')
    } catch (e) {}
  }
  if (iframeRef.value) {
    try {
      const doc = iframeRef.value.contentDocument || iframeRef.value.contentWindow?.document
      if (doc) {
        if (role === 'business') {
          doc.documentElement.classList.add('role-business')
          if (doc.body) doc.body.classList.add('role-business')
        } else {
          doc.documentElement.classList.remove('role-business')
          if (doc.body) doc.body.classList.remove('role-business')
        }
      }
    } catch (e) {}
  }
}

watch(selectedRole, () => {
  syncReportRole()
})

function handleIframeLoad() {
  syncReportRole()
  setTimeout(syncReportRole, 200)
  setTimeout(syncReportRole, 600)
}

function selectReport(report) {
  selectedReport.value = report
  currentReportUrl.value = `${report.report_url}?role=${selectedRole.value}&t=${Date.now()}`
}

function openInNewTab() {
  if (currentReportUrl.value) {
    window.open(currentReportUrl.value, '_blank')
  }
}

onMounted(() => {
  fetchHistoryReports()
})
</script>

<template>
  <div class="reports-platform-container">
    <!-- 质量门禁概览条 (动态数据驱动) -->
    <div class="metrics-bar">
      <div class="metric-item">
        <span class="m-label">自动化覆盖率</span>
        <span class="m-val" :class="metrics.coverage_is_passed ? 'text-success' : 'text-danger'">
          {{ metrics.coverage_rate }}%
        </span>
        <span class="m-target">门禁目标: &ge; {{ metrics.coverage_target }}% ({{ metrics.coverage_is_passed ? '达标' : '未达标' }})</span>
      </div>
      <div class="metric-item">
        <span class="m-label">冒烟测试通过率</span>
        <span class="m-val" :class="metrics.smoke_is_passed ? 'text-primary' : 'text-danger'">
          {{ metrics.smoke_pass_rate }}%
        </span>
        <span class="m-target">门禁目标: &ge; {{ metrics.smoke_target }}% ({{ metrics.smoke_is_passed ? '达标' : '未达标' }})</span>
      </div>
      <div class="metric-item">
        <span class="m-label">Flaky Test 占比</span>
        <span class="m-val" :class="metrics.flaky_is_healthy ? 'text-warning' : 'text-danger'">
          {{ metrics.flaky_rate }}%
        </span>
        <span class="m-target">门禁目标: &le; {{ metrics.flaky_target }}% ({{ metrics.flaky_is_healthy ? '健康' : '超标' }})</span>
      </div>
      <div class="metric-item">
        <span class="m-label">累计归档报告</span>
        <span class="m-val text-indigo">{{ historyReports.length }} 份</span>
        <span class="m-target">Allure 独立任务隔离</span>
      </div>
    </div>

    <!-- 报告主体：左侧历史列表 + 右侧报告浏览 -->
    <div class="reports-body">
      <!-- 左侧历史列表 -->
      <aside class="history-sidebar">
        <div class="history-header">
          <span>📑 历史执行任务报告</span>
          <el-button size="small" circle :icon="'Refresh'" @click="fetchHistoryReports" />
        </div>

        <div v-if="historyReports.length > 0" class="history-list">
          <div
            v-for="item in historyReports"
            :key="item.task_id"
            class="history-item"
            :class="{ active: selectedReport?.task_id === item.task_id }"
            @click="selectReport(item)"
          >
            <div class="h-title">
              <span class="h-tag">Allure</span>
              <span class="h-id">{{ item.task_id }}</span>
            </div>
            <div class="h-time">{{ item.time }}</div>
          </div>
        </div>
        <div v-else class="empty-history">
          暂无历史生成的测试报告
        </div>
      </aside>

      <!-- 右侧宽幅报告浏览 -->
      <section class="report-viewer">
        <div class="viewer-header">
          <div class="v-left">
            <span class="v-title">当前报告: {{ selectedReport ? selectedReport.task_id : '就绪' }}</span>
            <span v-if="selectedReport" class="v-time">生成时间: {{ selectedReport.time }}</span>
          </div>
          <div class="v-actions">
            <el-select
              v-model="selectedRole"
              size="small"
              style="width: 140px; margin-right: 10px;"
              @change="syncReportRole"
            >
              <el-option label="精简视角" value="business" />
              <el-option label="完整视角" value="tech" />
            </el-select>
            <el-button size="small" type="primary" plain @click="openInNewTab">
              新窗口全屏打开
            </el-button>
          </div>
        </div>

        <div class="iframe-box">
          <iframe
            v-if="currentReportUrl"
            ref="iframeRef"
            :src="currentReportUrl"
            class="report-iframe"
            @load="handleIframeLoad"
          ></iframe>
          <div v-else class="no-report">
            <el-icon :size="48" style="color: #cbd5e1;"><DataAnalysis /></el-icon>
            <p>请选择左侧历史报告，或在测试控制台中运行新测试</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.reports-platform-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 14px;
  padding: 16px 20px;
  box-sizing: border-box;
  overflow: hidden;
}

.metrics-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.metric-item {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  padding: 12px 18px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
}

.m-label {
  font-size: 12px;
  color: #64748b;
}

.m-val {
  font-size: 22px;
  font-weight: 700;
  font-family: var(--font-mono);
  margin: 4px 0 2px 0;
}

.m-target {
  font-size: 11px;
  color: #94a3b8;
}

.text-success { color: #059669; }
.text-primary { color: #2563eb; }
.text-warning { color: #d97706; }
.text-indigo { color: #7c3aed; }

.reports-body {
  flex: 1;
  display: flex;
  gap: 14px;
  overflow: hidden;
}

.history-sidebar {
  width: 280px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-header {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.history-item {
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.history-item:hover {
  background: #fff;
  border-color: rgba(37, 99, 235, 0.2);
}

.history-item.active {
  background: #eff6ff;
  border-color: #2563eb;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.h-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.h-tag {
  font-size: 10px;
  background: #2563eb;
  color: #fff;
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 600;
}

.h-id {
  font-size: 12px;
  font-family: var(--font-mono);
  font-weight: 600;
  color: #0f172a;
}

.h-time {
  font-size: 11px;
  color: #64748b;
  margin-top: 4px;
}

.empty-history {
  padding: 30px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
}

.report-viewer {
  flex: 1;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.viewer-header {
  padding: 12px 18px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.v-title {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  margin-right: 12px;
}

.v-time {
  font-size: 12px;
  color: #64748b;
}

.iframe-box {
  flex: 1;
  background: #fff;
  position: relative;
}

.report-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.no-report {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #64748b;
  gap: 12px;
}
</style>
