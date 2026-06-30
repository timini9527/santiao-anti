<template>
  <el-container class="shell">
    <el-aside width="420px" class="sidebar">
      <div class="brand-row">
        <div>
          <h1>Santiao 自动化测试</h1>
          <p>{{ health.project_root || '连接后端中...' }}</p>
        </div>
        <el-button :icon="Refresh" circle @click="refreshAll" />
      </div>

      <el-input
        v-model="keyword"
        :prefix-icon="Search"
        placeholder="搜索用例名称、nodeid、文件路径"
        clearable
        class="search"
      />

      <div class="tree-toolbar">
        <el-tag type="info">共 {{ filteredCases.length }} 条</el-tag>
        <el-switch v-model="hideDestructive" active-text="隐藏破坏性用例" />
      </div>

      <el-scrollbar class="test-tree">
        <el-tree
          ref="treeRef"
          :data="filteredTree"
          node-key="id"
          :props="{ label: 'label', children: 'children' }"
          :expand-on-click-node="false"
          highlight-current
          default-expand-all
          @node-click="handleNodeClick"
        >
          <template #default="{ data }">
            <span class="tree-node" :class="`node-${data.type}`">
              <el-icon v-if="data.type === 'folder'"><Folder /></el-icon>
              <el-icon v-else-if="data.type === 'file'"><Document /></el-icon>
              <el-icon v-else-if="data.type === 'class'"><Collection /></el-icon>
              <el-icon v-else><VideoPlay /></el-icon>
              <span>{{ data.label }}</span>
              <el-tag v-if="data.case?.destructive" size="small" type="danger">destructive</el-tag>
            </span>
          </template>
        </el-tree>
      </el-scrollbar>
    </el-aside>

    <el-main class="main">
      <section class="top-grid">
        <div class="panel selected-panel">
          <div class="panel-title">
            <span>当前用例</span>
            <el-tag v-if="selectedCase" :type="selectedCase.destructive ? 'danger' : 'success'">
              {{ selectedCase.destructive ? '高风险' : '可执行' }}
            </el-tag>
          </div>
          <template v-if="selectedCase">
            <h2>{{ selectedCase.display_name }}</h2>
            <p class="nodeid">{{ selectedNodeid }}</p>
            <div class="meta-row">
              <span>文件：{{ selectedCase.file }}</span>
              <span>函数：{{ selectedCase.function_name }}</span>
            </div>
            <el-select
              v-if="selectedCase.params.length"
              v-model="selectedParamNodeid"
              placeholder="选择参数化用例"
              class="param-select"
            >
              <el-option :label="`全部参数：${selectedCase.function_name}`" :value="selectedCase.nodeid" />
              <el-option
                v-for="param in selectedCase.params"
                :key="param.nodeid"
                :label="param.label"
                :value="param.nodeid"
              />
            </el-select>
          </template>
          <el-empty v-else description="从左侧选择一条用例" />
        </div>

        <div class="panel">
          <div class="panel-title">运行配置</div>
          <el-form label-position="top" class="run-form">
            <el-row :gutter="12">
              <el-col :span="8">
                <el-form-item label="环境">
                  <el-input v-model="form.env" placeholder="如 test / dev" clearable />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Appium 地址">
                  <el-input v-model="form.remote_appium" placeholder="http://127.0.0.1:4723" clearable />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="设备 UDID">
                  <el-input v-model="form.remote_udid" placeholder="emulator-5554" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="8">
                <el-form-item label="单聊对象">
                  <el-input v-model="form.private_chat_name" clearable />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="群聊对象">
                  <el-input v-model="form.group_chat_name" clearable />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="调试模式">
                  <el-switch v-model="form.debug_mode" active-text="开启 pdb" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="回执/自定义数据">
              <el-input v-model="form.web_receipt_data" type="textarea" :rows="2" clearable />
            </el-form-item>
          </el-form>
          <div class="action-row">
            <el-button type="primary" :icon="VideoPlay" :disabled="!selectedCase || running" @click="startRun">
              执行用例
            </el-button>
            <el-button type="danger" :icon="CircleClose" :disabled="!running" @click="stopCurrentTask">
              停止
            </el-button>
            <el-button :icon="Refresh" @click="loadTasks">刷新历史</el-button>
          </div>
        </div>
      </section>

      <section class="content-grid">
        <div class="panel console-panel">
          <div class="panel-title">
            <span>实时日志</span>
            <el-tag :type="statusTagType">{{ currentStatusText }}</el-tag>
          </div>
          <pre ref="consoleRef" class="console">{{ logs.join('\n') }}</pre>
        </div>

        <div class="panel history-panel">
          <div class="panel-title">最近执行</div>
          <el-scrollbar class="history-list">
            <div v-for="task in tasks" :key="task.task_id" class="history-item" @click="loadTaskTail(task)">
              <div class="history-head">
                <el-tag :type="taskType(task.status)" size="small">{{ statusLabel(task.status) }}</el-tag>
                <span>{{ task.task_id }}</span>
              </div>
              <p>{{ task.nodeid }}</p>
              <small>{{ task.started_at }}</small>
            </div>
            <el-empty v-if="!tasks.length" description="暂无执行记录" />
          </el-scrollbar>
        </div>
      </section>
    </el-main>
  </el-container>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CircleClose,
  Collection,
  Document,
  Folder,
  Refresh,
  Search,
  VideoPlay
} from '@element-plus/icons-vue'
import { getHealth, getTasks, getTests, runTest, stopTask } from './api'

const health = reactive({})
const cases = ref([])
const tree = ref([])
const tasks = ref([])
const keyword = ref('')
const hideDestructive = ref(true)
const selectedCase = ref(null)
const selectedParamNodeid = ref('')
const currentTaskId = ref('')
const currentStatus = ref('idle')
const logs = ref([])
const consoleRef = ref(null)
const eventSource = ref(null)

const form = reactive({
  env: '',
  remote_appium: '',
  remote_udid: '',
  debug_mode: false,
  private_chat_name: '',
  group_chat_name: '',
  web_receipt_data: ''
})

const running = computed(() => currentStatus.value === 'running')
const selectedNodeid = computed(() => selectedParamNodeid.value || selectedCase.value?.nodeid || '')

const filteredCases = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return cases.value.filter((item) => {
    if (hideDestructive.value && item.destructive) return false
    if (!text) return true
    return [item.display_name, item.nodeid, item.file, item.module]
      .filter(Boolean)
      .some((value) => value.toLowerCase().includes(text))
  })
})

const filteredTree = computed(() => buildTree(filteredCases.value))

const currentStatusText = computed(() => statusLabel(currentStatus.value))
const statusTagType = computed(() => taskType(currentStatus.value))

function buildTree(items) {
  const roots = new Map()
  const ensureChild = (parent, id, label, type) => {
    let child = parent.children.find((item) => item.id === id)
    if (!child) {
      child = { id, label, type, children: [] }
      parent.children.push(child)
    }
    return child
  }

  for (const item of items) {
    const parts = item.file.split('/')
    const rootName = parts[0]
    if (!roots.has(rootName)) roots.set(rootName, { id: rootName, label: rootName, type: 'folder', children: [] })
    let parent = roots.get(rootName)
    for (const part of parts.slice(1, -1)) {
      parent = ensureChild(parent, `${parent.id}/${part}`, part, 'folder')
    }
    const fileNode = ensureChild(parent, item.file, parts.at(-1), 'file')
    let caseParent = fileNode
    if (item.class_name) {
      caseParent = ensureChild(fileNode, `${item.file}::${item.class_name}`, item.class_name, 'class')
    }
    caseParent.children.push({ id: item.id, label: item.display_name, type: 'case', case: item, children: [] })
  }
  return Array.from(roots.values())
}

function handleNodeClick(data) {
  if (data.type !== 'case') return
  selectedCase.value = data.case
  selectedParamNodeid.value = data.case.nodeid
}

async function refreshAll() {
  await Promise.all([loadHealth(), loadTests(), loadTasks()])
}

async function loadHealth() {
  Object.assign(health, await getHealth())
}

async function loadTests() {
  const data = await getTests()
  cases.value = data.cases
  tree.value = data.tree
}

async function loadTasks() {
  const data = await getTasks()
  tasks.value = data.tasks || []
}

async function startRun() {
  if (!selectedNodeid.value) return
  logs.value = []
  currentStatus.value = 'running'
  closeEventSource()
  try {
    const payload = {
      ...form,
      nodeid: selectedNodeid.value
    }
    const data = await runTest(payload)
    currentTaskId.value = data.task_id
    connectLogs(data.task_id)
    await loadTasks()
    ElMessage.success(data.message)
  } catch (error) {
    currentStatus.value = 'failed'
    ElMessage.error(error.message)
  }
}

async function stopCurrentTask() {
  if (!currentTaskId.value) return
  try {
    await stopTask(currentTaskId.value)
    currentStatus.value = 'stopped'
    await loadTasks()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

function connectLogs(taskId) {
  eventSource.value = new EventSource(`/api/logs/stream/${taskId}`)
  eventSource.value.onmessage = async (event) => {
    const payload = JSON.parse(event.data)
    if (payload.type === 'log') {
      logs.value.push(payload.line)
      await nextTick()
      if (consoleRef.value) consoleRef.value.scrollTop = consoleRef.value.scrollHeight
    }
    if (payload.type === 'status') {
      currentStatus.value = payload.status
      closeEventSource()
      await loadTasks()
    }
  }
  eventSource.value.onerror = () => {
    if (running.value) logs.value.push('日志连接中断，浏览器将保留当前输出。')
    closeEventSource()
  }
}

function closeEventSource() {
  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }
}

function loadTaskTail(task) {
  currentTaskId.value = task.task_id
  currentStatus.value = task.status
  logs.value = task.log_tail || []
}

function statusLabel(status) {
  return {
    idle: '未执行',
    queued: '排队中',
    running: '执行中',
    finished: '通过',
    failed: '失败',
    stopped: '已停止'
  }[status] || status
}

function taskType(status) {
  return {
    idle: 'info',
    queued: 'warning',
    running: 'primary',
    finished: 'success',
    failed: 'danger',
    stopped: 'warning'
  }[status] || 'info'
}

onMounted(refreshAll)
</script>
