<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// ==================== 1. 响应式状态定义 ====================
const taskId = ref('task_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now())
const catalog = ref([])                     // 测试用例树数据
const defaultExpandedKeys = ref([])         // 默认展开的节点 key 列表
const filterText = ref('')                  // 模糊过滤文本
const treeRef = ref(null)                   // el-tree DOM 引用
const isRunning = ref(false)                // 测试任务锁
const runningCaseName = ref('')             // 当前正在运行的用例名称
const globalStatus = ref('idle')            // 全局状态: idle, running, success, danger
const globalStatusText = ref('就绪')        // 全局状态文字

// 状态本地持久化存储机制（刷新网页或重启软件后自动保留当前选中的所有设备与配置）
const STORAGE_KEY_PREFIX = 'ST_MOBILE_CONFIG_'

function getStored(key, defaultValue) {
  try {
    const val = localStorage.getItem(STORAGE_KEY_PREFIX + key)
    if (val !== null && val !== undefined && val !== '') {
      if (typeof defaultValue === 'boolean') return val === 'true'
      return val
    }
  } catch (e) {}
  return defaultValue
}

function setStored(key, value) {
  try {
    localStorage.setItem(STORAGE_KEY_PREFIX + key, String(value ?? ''))
  } catch (e) {}
}

// 接口及移动端配置参数（持久化响应式对象）
const osSelect = ref(getStored('OS', 'windows'))
const remoteAppium = ref(getStored('APPIUM1', '127.0.0.1:4723'))
const remoteAppium2 = ref(getStored('APPIUM2', '127.0.0.1:4724'))
const remoteUdid = ref(getStored('UDID1', 'QFF0219A11009305'))
const remoteUdid2 = ref(getStored('UDID2', '20a5fa17'))
const privateChatName = ref(getStored('PRIVATE_CHAT', ''))
const groupChatName = ref(getStored('GROUP_CHAT', ''))
const debugMode = ref(getStored('DEBUG_MODE', false))
const onlineDevices = ref([])
const onlineDeviceItems = ref([])
const realDeviceUdids = ref([])

// 自动监听并在每次用户选择/输入变更时实时持久化
watch(osSelect, (v) => setStored('OS', v))
watch(remoteAppium, (v) => setStored('APPIUM1', v))
watch(remoteAppium2, (v) => setStored('APPIUM2', v))
watch(remoteUdid, (v) => setStored('UDID1', v))
watch(remoteUdid2, (v) => setStored('UDID2', v))
watch(privateChatName, (v) => setStored('PRIVATE_CHAT', v))
watch(groupChatName, (v) => setStored('GROUP_CHAT', v))
watch(debugMode, (v) => setStored('DEBUG_MODE', v))

// 设备下拉选项列表（聚合真实 USB 真机、默认双机及在线模拟器，保证选项纯净无杂质）
const deviceOptionList = computed(() => {
  const map = new Map()

  // 1. 真实 USB 真机及探测到的设备置顶
  if (onlineDeviceItems.value && onlineDeviceItems.value.length > 0) {
    onlineDeviceItems.value.forEach(item => {
      map.set(item.udid, {
        udid: item.udid,
        desc: item.desc || (item.is_real ? 'USB真机' : '在线设备'),
        is_real: item.is_real
      })
    })
  }

  // 2. 默认发送端 (若未在列表中则追加)
  if (!map.has('QFF0219A11009305')) {
    map.set('QFF0219A11009305', {
      udid: 'QFF0219A11009305',
      desc: '默认发送端',
      is_real: false
    })
  }

  // 3. 默认接收端 (若未在列表中则追加)
  if (!map.has('20a5fa17')) {
    map.set('20a5fa17', {
      udid: '20a5fa17',
      desc: '默认接收端',
      is_real: false
    })
  }

  // 4. 确保当前输入框内的自定义输入也在列表中，防止回显异常
  if (remoteUdid.value && !map.has(remoteUdid.value)) {
    map.set(remoteUdid.value, {
      udid: remoteUdid.value,
      desc: '当前选择 (发送端)',
      is_real: false
    })
  }
  if (remoteUdid2.value && !map.has(remoteUdid2.value)) {
    map.set(remoteUdid2.value, {
      udid: remoteUdid2.value,
      desc: '当前选择 (接收端)',
      is_real: false
    })
  }

  return Array.from(map.values())
})

// 本机局域网真实有效 IP（由后台动态获取注入，自适应任何网络环境）
const localHostIp = ref('')

// 动态 Appium 1 地址下拉选项（支持本地、动态局域网与自定义输入）
const appium1Options = computed(() => {
  const options = [{ label: '127.0.0.1:4723 (本地)', value: '127.0.0.1:4723' }]
  if (localHostIp.value && localHostIp.value !== '127.0.0.1') {
    options.push({ label: `${localHostIp.value}:4723 (局域网本机)`, value: `${localHostIp.value}:4723` })
  }
  if (remoteAppium.value && !options.some(o => o.value === remoteAppium.value)) {
    options.push({ label: remoteAppium.value, value: remoteAppium.value })
  }
  return options
})

// 动态 Appium 2 地址下拉选项（支持本地、动态局域网与自定义输入）
const appium2Options = computed(() => {
  const options = [{ label: '127.0.0.1:4724 (本地)', value: '127.0.0.1:4724' }]
  if (localHostIp.value && localHostIp.value !== '127.0.0.1') {
    options.push({ label: `${localHostIp.value}:4724 (局域网本机)`, value: `${localHostIp.value}:4724` })
  }
  if (remoteAppium2.value && !options.some(o => o.value === remoteAppium2.value)) {
    options.push({ label: remoteAppium2.value, value: remoteAppium2.value })
  }
  return options
})

// Allure 报告相关
const reportUrl = ref('')
const selectedRole = ref(getStored('ROLE', 'business'))
watch(selectedRole, (v) => setStored('ROLE', v))
const iframeRef = ref(null)

// 终端日志
const logsBuffer = ref('等待选择用例并运行...')
const terminalScreenRef = ref(null)
let activeSse = null
let statusInterval = null

// 计算属性：对日志内容做 HTML 安全转义和 ANSI 转义字符着色，并使 info/error/warning/debug 颜色与 logger_utils.py 配置高度一致
const formattedLogs = computed(() => {
  if (!logsBuffer.value) return ''
  let html = logsBuffer.value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')

  // 匹配 \x1b[ 或是 \u001b[ 这种标准 ANSI 转义码
  html = html
    .replace(/\x1b\[[0-9;]*31m/g, '<span style="color:#e11d48;font-weight:bold;">') // bold_red (ERROR) -> 胭脂红
    .replace(/\x1b\[[0-9;]*32m/g, '<span style="color:#059669;font-weight:bold;">') // bold_green (INFO) -> 极光绿
    .replace(/\x1b\[[0-9;]*33m/g, '<span style="color:#d97706;font-weight:bold;">') // bold_yellow (WARNING) -> 焦糖黄
    .replace(/\x1b\[[0-9;]*34m/g, '<span style="color:#2563eb;font-weight:bold;">') // bold_blue -> 皇家蓝
    .replace(/\x1b\[[0-9;]*35m/g, '<span style="color:#7c3aed;font-weight:bold;">') // bold_magenta -> 藕荷紫
    .replace(/\x1b\[[0-9;]*36m/g, '<span style="color:#0891b2;font-weight:bold;">') // bold_cyan (DEBUG) -> 青蓝
    .replace(/\x1b\[[0-9;]*37m/g, '<span style="color:#475569;font-weight:bold;">') // bold_white -> 深灰
    .replace(/\x1b\[[0-9;]*90m/g, '<span style="color:#64748b;">')                   // gray -> 浅灰
    .replace(/\x1b\[[0-9;]*m/g, '</span>')
    // 消除其他转义
    .replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '')
    .replace(/\x1b/g, '')

  // 兜底正则匹配：在日志纯文本中寻找级别关键字并着色高亮（对应 logger_utils.py）
  html = html
    .replace(/\[DEBUG\]/g, '<span style="color:#0891b2;font-weight:bold;">[DEBUG]</span>')
    .replace(/\[INFO\]/g, '<span style="color:#059669;font-weight:bold;">[INFO]</span>')
    .replace(/\[WARNING\]/g, '<span style="color:#d97706;font-weight:bold;">[WARNING]</span>')
    .replace(/\[ERROR\]/g, '<span style="color:#e11d48;font-weight:bold;">[ERROR]</span>')
    .replace(/\[CRITICAL\]/g, '<span style="color:#e11d48;font-weight:bold;text-decoration:underline;">[CRITICAL]</span>')

  return html
})

// Web 回执弹窗与数据
const isReceiptVisible = ref(false)
const receiptFields = ref([
    { key: "设备1", val: "" },
    { key: "私聊用户1", val: "" },
    { key: "私聊用户2", val: "" },
    { key: "群聊名称1", val: "" },
    { key: "群聊名称2", val: "" }
])

// 拖拽宽度与高度
const sidebarWidth = ref(380)
const reportHeight = ref(450)
const paramsPanelHeight = ref(420) // 默认提供 420px 容纳多个输入框
const isResizingH = ref(false)
const isResizingV = ref(false)
const isResizingParams = ref(false)

// 终端自动滚屏与日志控制
const autoScroll = ref(true)

// 参数面板折叠状态与高度缓存
const isParamsCollapsed = ref(false)
const savedParamsHeight = ref(420)

// ==================== 2. 页面加载初始化 ====================
onMounted(() => {
    // 强制开启 Element Plus 暗黑主题
    // document.documentElement.classList.add('dark')
    // 启用高级浅色珍珠白主题
    document.documentElement.classList.remove('dark')
  
    loadTestsCatalog()
    initDeviceDetectors()
    startStatusPolling()
})

onUnmounted(() => {
  if (activeSse) activeSse.close()
  if (statusInterval) clearInterval(statusInterval)
})

// 监听搜索词变化，触发 ElTree 过滤，并在过滤后强制折叠所有文件节点防止自动展开用例
watch(filterText, (val) => {
  treeRef.value?.filter(val)
  if (val && treeRef.value) {
    // 过滤后，强行将所有测试文件节点折叠收起，阻止其因为子节点匹配而自动展开所有用例
    const nodesMap = treeRef.value.store.nodesMap
    for (const key in nodesMap) {
      const nd = nodesMap[key]
      if (nd.data && nd.data.isFile) {
        nd.collapse()
      }
    }
  }
})

// ==================== 3. 接口数据获取（改造成 index.html 的同等 Category 分组格式） ====================

// 载入并映射用例树数据
async function loadTestsCatalog() {
  try {
    const res = await fetch('/api/tests')
    if (!res.ok) throw new Error("获取测试用例列表失败")
    const rawCatalog = await res.json()
    
    // 初始化分类容器与根文件列表
    const categories = {}
    const directFiles = []
    
    rawCatalog.forEach(fileObj => {
      const file = fileObj.file
      let rel = file.startsWith('tests/') ? file.substring(6) : file
      let parts = rel.split('/')
      
      let fileCount = 0
      const fileChildren = []
      
      // 1. 映射 Class 及 Class 下的用例
      if (fileObj.classes && fileObj.classes.length > 0) {
        fileObj.classes.forEach(cls => {
          let classCount = 0
          const classChildren = []
          
          cls.tests.forEach(test => {
            const hasParams = test.params && test.params.length > 0
            if (hasParams) {
              classCount += test.params.length
              fileCount += test.params.length
              // 参数化测试组节点 (👻 图标)
              classChildren.push({
                id: `group::${file}::${cls.name}::${test.name}`,
                label: test.display_name || test.name,
                nodeid: `${file}::${cls.name}::${test.name}`,
                isTestGroup: true,
                count: test.params.length,
                children: test.params.map((param, pIdx) => ({
                  id: `param::${file}::${cls.name}::${test.name}[${param}]`,
                  label: param,
                  nodeid: `${file}::${cls.name}::${test.name}[${param}]`,
                  paramIndex: pIdx,
                  isTestParam: true
                }))
              })
            } else {
              classCount += 1
              fileCount += 1
              // 普通叶子用例节点 (⚙️ 图标)
              classChildren.push({
                id: `test::${file}::${cls.name}::${test.name}`,
                label: test.display_name || test.name,
                nodeid: `${file}::${cls.name}::${test.name}`,
                isTest: true
              })
            }
          })
          
          fileChildren.push({
            id: `class::${file}::${cls.name}`,
            label: cls.display_name,
            isClass: true,
            file: file,
            className: cls.name,
            nodeid: `${file}::${cls.name}`,
            children: classChildren
          })
        })
      }
      
      // 2. 映射独立测试函数 (如 test_standalone)
      if (fileObj.tests && fileObj.tests.length > 0) {
        fileObj.tests.forEach(test => {
          const hasParams = test.params && test.params.length > 0
          if (hasParams) {
            fileCount += test.params.length
            // 参数化测试组节点 (👻 图标)
            fileChildren.push({
              id: `group::${file}::${test.name}`,
              label: test.display_name || test.name,
              nodeid: `${file}::${test.name}`,
              isTestGroup: true,
              count: test.params.length,
              children: test.params.map((param, pIdx) => ({
                id: `param::${file}::${test.name}[${param}]`,
                label: param,
                nodeid: `${file}::${test.name}[${param}]`,
                paramIndex: pIdx,
                isTestParam: true
              }))
            })
          } else {
            fileCount += 1
            // 普通叶子用例节点 (⚙️ 图标)
            fileChildren.push({
              id: `test::${file}::${test.name}`,
              label: test.display_name || test.name,
              nodeid: `${file}::${test.name}`,
              isTest: true
            })
          }
        })
      }
      
      // 文件节点定义
      const fileNode = {
        id: `file::${file}`,
        label: fileObj.display_name,
        isFile: true,
        file: file,
        count: fileCount,
        children: fileChildren
      }
      
      if (parts.length > 1) {
        // 如果文件在 tests/ 目录的子文件夹中，将其划归至对应的 Category 下
        const catName = parts[0]
        if (!categories[catName]) {
          categories[catName] = []
        }
        categories[catName].push(fileNode)
      } else {
        // 直接在 tests/ 根目录下的独立测试文件
        directFiles.push(fileNode)
      }
    })
    
    const finalTreeData = []
    
    // 渲染排序后的分类目录并统计子目录用例总和
    const sortedCatNames = Object.keys(categories).sort((a, b) => {
      if (a === 'smoke_test') return -1
      if (b === 'smoke_test') return 1
      return a.localeCompare(b)
    })
    sortedCatNames.forEach(catName => {
      let catCount = 0
      categories[catName].forEach(f => {
        catCount += f.count
      })
      
      finalTreeData.push({
        id: `category::${catName}`,
        label: catName,
        isCategory: true,
        count: catCount,
        children: categories[catName]
      })
    })
    
    // 渲染独立的文件节点
    directFiles.forEach(f => {
      finalTreeData.push(f)
    })
    
    catalog.value = finalTreeData
    
    // 默认状态下仅展开第一个顶级节点（即置顶的 smoke_test，露出其下的第二级文件节点）
    if (finalTreeData.length > 0) {
      defaultExpandedKeys.value = [finalTreeData[0].id]
    }
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 模糊过滤节点判断：仅对目录或文件名进行过滤，且三级用例节点不被隐藏（但其自身不匹配以防触发自动展开）
function filterNode(value, data, node) {
  if (!value) return true
  
  // 1. 若是目录分类节点，自身匹配则保留
  if (data.isCategory) {
    return data.label.toLowerCase().includes(value.toLowerCase())
  }
  
  // 2. 若是测试文件节点，自身文件名匹配则保留
  if (data.isFile) {
    return data.label.toLowerCase().includes(value.toLowerCase())
  }
  
  // 3. 所有更深层级的类、用例、参数等子节点，只要其所属的测试文件匹配，就保留，不被隐藏
  let parentNode = node.parent
  while (parentNode) {
    if (parentNode.data && parentNode.data.isFile) {
      return parentNode.data.label.toLowerCase().includes(value.toLowerCase())
    }
    parentNode = parentNode.parent
  }
  
  return false
}

// 全局独占展开逻辑：只允许展开当前操作的这一条直系链路，收起所有其他无关的树节点
function handleNodeExpand(data, node) {
  if (!treeRef.value) return
  
  // 1. 收集当前节点及其所有直系祖先节点的 key，放入白名单
  const activeKeys = new Set()
  let curr = node
  while (curr && curr.key) {
    activeKeys.add(curr.key)
    curr = curr.parent
  }
  
  // 2. 遍历 el-tree 内存里的所有节点，将不在白名单内的已展开节点强制折叠
  const nodesMap = treeRef.value.store.nodesMap
  for (const key in nodesMap) {
    const nd = nodesMap[key]
    if (nd.expanded && !activeKeys.has(nd.key)) {
      nd.collapse()
    }
  }
}

// 一键全部展开 / 全部折叠用例树
function toggleExpandAll(expand) {
  if (!treeRef.value) return
  const nodesMap = treeRef.value.store.nodesMap
  for (const key in nodesMap) {
    if (expand) {
      nodesMap[key].expand()
    } else {
      nodesMap[key].collapse()
    }
  }
}

// ==================== 4. 移动端与 Appium 自动探测 ====================

async function initDeviceDetectors() {
  detectAppiumStatus(4723)
  detectAppiumStatus(4724)
  try {
    const res = await fetch('/api/detect_udid', { method: 'POST' })
    const data = await res.json()
    if (data.device_items) {
      onlineDeviceItems.value = data.device_items
    }
    if (data.real_devices) {
      realDeviceUdids.value = data.real_devices
    }
    if (data.devices) {
      onlineDevices.value = data.devices
    }
    // 保持初始默认绑定的发送端与接收端 UDID，不强制冲掉输入框预设，待用户主动点击“检测真机”或下拉切换
  } catch (e) {
    console.warn("初始化探测双机设备失败", e)
  }
}

async function detectAppiumStatus(port = 4723) {
  try {
    const res = await fetch('/api/detect_appium', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ port })
    })
    const data = await res.json()
    if (data.local_ip) {
      localHostIp.value = data.local_ip
    }
    if (data.appium) {
      if (port === 4723) {
        remoteAppium.value = data.appium
      } else if (port === 4724) {
        remoteAppium2.value = data.appium
      }
      ElMessage.success(`探测端口 ${port} 成功，Appium 服务可用`)
    } else {
      ElMessage.warning(`端口 ${port} 探测完毕：当前未运行 Appium 监听`)
    }
  } catch (e) {
    console.warn(`探测 Appium 端口 ${port} 失败`, e)
  }
}

async function triggerStartAppium(port = 4723) {
  try {
    const res = await fetch('/api/start_appium', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ os: osSelect.value, port })
    })
    const data = await res.json()
    if (data.success) {
      ElMessage.success(`已请求后台拉起 Appium 进程，正在监听 ${port} 端口...`)
      setTimeout(() => {
        detectAppiumStatus(port)
      }, 3000)
    }
  } catch (e) {
    ElMessage.error(`调起 Appium (端口 ${port}) 异常: ` + e.message)
  }
}

async function detectConnectedDevices(targetIndex = 1) {
  try {
    const res = await fetch('/api/detect_udid', { method: 'POST' })
    const data = await res.json()
    
    if (data.device_items) {
      onlineDeviceItems.value = data.device_items
    }
    if (data.real_devices) {
      realDeviceUdids.value = data.real_devices
    }
    if (data.devices) {
      onlineDevices.value = data.devices
    }
    
    const realList = data.real_devices || []
    const allList = data.all_devices || []
    
    if (targetIndex === 1) {
      // 点击第一部手机的【检测真机】：优先获取第 1 台真实物理 USB 手机，直接替换掉原默认设备
      if (realList.length > 0) {
        remoteUdid.value = realList[0]
        ElMessage.success(`✅ 已直接获取 USB 连接真机并替换发送端: ${remoteUdid.value}`)
      } else if (allList.length > 0) {
        remoteUdid.value = allList[0]
        ElMessage.info(`未检测到 USB 物理真机，已获取在线设备并替换发送端: ${remoteUdid.value}`)
      } else {
        ElMessage.warning("未检测到任何 USB 连接设备，请检查手机数据线与开发者 USB 调试开关！")
      }
    } else {
      // 点击第二部手机的【检测真机】：获取第 2 台真实物理 USB 手机，直接替换掉原默认设备
      if (realList.length >= 2) {
        remoteUdid2.value = realList[1]
        ElMessage.success(`✅ 已直接获取 USB 连接第 2 台真机并替换接收端: ${remoteUdid2.value}`)
      } else if (realList.length === 1) {
        const singleReal = realList[0]
        if (remoteUdid.value === singleReal) {
          // 当前唯一物理真机已被发送端占用
          const emuList = data.emulator_devices || []
          if (emuList.length > 0) {
            remoteUdid2.value = emuList[0]
            ElMessage.warning(`仅检测到 1 台 USB 真机[${singleReal}]（已设为发送端），接收端已自动匹配可用模拟器: ${remoteUdid2.value}`)
          } else {
            remoteUdid2.value = singleReal
            ElMessage.warning(`仅检测到 1 台 USB 真机[${singleReal}]，已同步替换接收端。若需双机并发测试请插入第二台手机。`)
          }
        } else {
          remoteUdid2.value = singleReal
          ElMessage.success(`✅ 已直接获取 USB 连接真机并替换接收端: ${remoteUdid2.value}`)
        }
      } else if (allList.length > 0) {
        const fallback = allList.length > 1 ? allList[1] : allList[0]
        remoteUdid2.value = fallback
        ElMessage.info(`未检测到 USB 物理真机，已获取在线设备并替换接收端: ${remoteUdid2.value}`)
      } else {
        ElMessage.warning("未检测到任何 USB 连接设备，请检查手机数据线与开发者 USB 调试开关！")
      }
    }
  } catch (e) {
    ElMessage.error("检测手机 UDID 失败: " + e.message)
  }
}

// 互换发送端与接收端的手机 UDID
function swapDevices() {
  const temp = remoteUdid.value
  remoteUdid.value = remoteUdid2.value
  remoteUdid2.value = temp
  ElMessage.success(`已对调：发送端[${remoteUdid.value}] ⇄ 接收端[${remoteUdid2.value}]`)
}


// ==================== 5. 用例执行控制 ====================
async function startTestExecution(node) {
  if (isRunning.value) return

  resetAllNodesStatus(catalog.value)

  isRunning.value = true
  globalStatus.value = 'running'
  globalStatusText.value = '运行中'
  
  // 按照不同的节点层级拼接对应的 nodeid 和参数信息下发后端
  let targetNodeId = ""
  let paramIdx = null
  
  if (node.isCategory) {
    // 运行整个目录
    targetNodeId = `tests/${node.label}`
  } else if (node.isFile) {
    // 运行整个文件
    targetNodeId = node.file
  } else if (node.isClass) {
    // 运行整个类
    targetNodeId = node.nodeid
  } else if (node.isTestGroup) {
    // 运行参数化函数的整个组
    targetNodeId = node.nodeid
  } else if (node.isTestParam) {
    // 运行参数化的单个实例
    targetNodeId = node.nodeid
    paramIdx = node.paramIndex
  } else if (node.isTest) {
    // 运行普通独立测试
    targetNodeId = node.nodeid
  }
  
  // 每次触发运行生成独立全新的任务ID，确保报告与状态隔离
  taskId.value = 'task_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now()
  runningCaseName.value = node.label.split(' (')[0]
  logsBuffer.value = `[Web Console] 🚀 正在向后端下发测试任务:\n用例: ${targetNodeId}\n任务ID: ${taskId.value}\n----------------------------------------\n`
  
  // 转换回执数据为 JSON 字符串
  const receiptData = {}
  receiptFields.value.forEach(f => {
    if (f.key.trim()) receiptData[f.key.trim()] = f.val
  })

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_id: taskId.value,
        nodeid: targetNodeId,
        param_index: paramIdx,
        remote_appium: remoteAppium.value,
        remote_appium2: remoteAppium2.value,
        remote_udid: remoteUdid.value,
        remote_udid2: remoteUdid2.value,
        debug_mode: debugMode.value,
        private_chat_name: privateChatName.value,
        group_chat_name: groupChatName.value,
        web_receipt_data: JSON.stringify(receiptData)
      })
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || "请求异常")
    }

    // 1. 建立 SSE 实时日志流通道
    connectSseStream()
    // 2. 调起状态轮询器（双保险感知任务完成）
    startStatusPolling()
  } catch (err) {
    logsBuffer.value += `\n⚠️ 启动任务失败: ${err.message}\n`
    isRunning.value = false
    globalStatus.value = 'danger'
    globalStatusText.value = '启动失败'
  }
}

function stripAnsi(str) {
  return str.replace(/[\u001b\x1b]\[[0-9;]*[a-zA-Z]/g, '')
}

function handleTaskFinished(exitCode = 0) {
  if (!isRunning.value) return
  isRunning.value = false

  if (statusInterval) {
    clearInterval(statusInterval)
    statusInterval = null
  }
  if (activeSse) {
    activeSse.close()
    activeSse = null
  }

  if (exitCode === 0) {
    globalStatus.value = 'success'
    globalStatusText.value = '测试通过'
    ElMessage.success("🎉 测试通过！")
  } else {
    globalStatus.value = 'danger'
    globalStatusText.value = `测试失败 (退出码:${exitCode})`
    ElMessage.error(`⚠️ 测试失败，退出码: ${exitCode}`)
  }

  // 自动刷新报告展示
  refreshReport()
}

async function checkTaskStatusNow() {
  try {
    const res = await fetch(`/api/status?task_id=${taskId.value}`)
    const data = await res.json()
    if (data.status === 'finished') {
      handleTaskFinished(data.exit_code ?? 0)
    }
  } catch (e) {
    console.error("立即检查任务状态异常: ", e)
  }
}

function connectSseStream() {
  if (activeSse) activeSse.close()
  
  activeSse = new EventSource(`/api/logs/stream?task_id=${taskId.value}`)
  
  // 1. 监听结构化 finished 事件
  activeSse.addEventListener('finished', (event) => {
    try {
      const data = JSON.parse(event.data)
      handleTaskFinished(data.exit_code ?? 0)
    } catch (e) {
      handleTaskFinished(0)
    }
  })

  // 2. 监听普通日志输出流
  activeSse.onmessage = (event) => {
    const logMsg = JSON.parse(event.data)
    logsBuffer.value += logMsg
    
    // 快速感知用例报告生成完毕或进程退出
    if (logMsg && (logMsg.includes("Allure 报告生成完毕") || logMsg.includes("测试执行与异常诊断报告生成完毕") || logMsg.includes("测试进程已退出"))) {
      setTimeout(checkTaskStatusNow, 400)
    }

    // 实时提取与解析用例执行状态
    if (logMsg) {
      const lines = logMsg.split(/[\r\n]+/);
      lines.forEach(line => {
        const cleanLine = stripAnsi(line).trim();
        if (!cleanLine) return;
        
        // 优先使用自定义插件打印的结构化 TEST_RESULT 行
        const pluginMatch = cleanLine.match(/\[TEST_RESULT\]\s+nodeid=([^\s]+)\s+status=([^\s]+)/i);
        if (pluginMatch) {
          const matchedNodeId = pluginMatch[1].trim();
          const rawStatus = pluginMatch[2].toLowerCase();
          
          let status = 'pending';
          if (rawStatus === 'passed') {
            status = 'passed';
          } else if (rawStatus === 'failed') {
            status = 'failed';
          } else if (rawStatus === 'skipped') {
            status = 'skipped';
          }
          
          updateNodeStatus(catalog.value, matchedNodeId, status);
          return;
        }
        
        // 兜底匹配 pytest 原生的控制台输出
        const match = cleanLine.match(/(tests\/[a-zA-Z0-9_\-\.\/]+\.py::[^\n\r]+?)\s+(PASSED|FAILED|ERROR|SKIPPED)/i);
        if (match) {
          const matchedNodeId = match[1].trim();
          const rawStatus = match[2].toUpperCase();
          
          let status = 'pending';
          if (rawStatus === 'PASSED') {
            status = 'passed';
          } else if (rawStatus === 'FAILED' || rawStatus === 'ERROR') {
            status = 'failed';
          } else if (rawStatus === 'SKIPPED') {
            status = 'skipped';
          }
          
          updateNodeStatus(catalog.value, matchedNodeId, status);
        }
      });
    }
    
    // 自动滚动终端到底部 (当开启 autoScroll 时吸底)
    if (autoScroll.value && terminalScreenRef.value) {
      terminalScreenRef.value.scrollTop = terminalScreenRef.value.scrollHeight
    }
  }
  
  activeSse.onerror = () => {
    // 发生网络错误时，立即尝试检查任务是否已正常结束
    checkTaskStatusNow()
    if (activeSse) {
      activeSse.close()
      activeSse = null
    }
  }
}

async function stopCurrentTask() {
  logsBuffer.value += `\n[Web Console] 🛑 正在请求强制终止测试任务...\n`
  try {
    const res = await fetch('/api/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId.value })
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || "终止失败")
    }
  } catch (e) {
    logsBuffer.value += `\n⚠️ 终止任务失败: ${e.message}\n`
  }
}

// 轮询运行状态（兜底保障机制）
function startStatusPolling() {
  if (statusInterval) clearInterval(statusInterval)
  statusInterval = setInterval(async () => {
    if (!isRunning.value) {
      if (statusInterval) {
        clearInterval(statusInterval)
        statusInterval = null
      }
      return
    }
    await checkTaskStatusNow()
  }, 1000)
}

// ==================== 6. Allure 报告视角联动 ====================

function refreshReport() {
  reportUrl.value = `/allure/${taskId.value}/index.html?role=${selectedRole.value}&t=${Date.now()}`
}

function syncReportRole() {
  const role = selectedRole.value

  // 通道 1: postMessage 广播（跨窗口解耦通知）
  if (iframeRef.value && iframeRef.value.contentWindow) {
    try {
      iframeRef.value.contentWindow.postMessage(`role:${role}`, '*')
      iframeRef.value.contentWindow.postMessage({ type: 'ALLURE_ROLE_SWITCH', role }, '*')
    } catch (e) {
      console.warn("postMessage 派发异常:", e)
    }
  }

  // 通道 2: 同源 DOM 深度直接穿透操作（立即生效，零延迟）
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

        // 动态检测并确保注入关键样式规则
        let styleTag = doc.getElementById('allure-role-controller-style')
        if (!styleTag && doc.head) {
          styleTag = doc.createElement('style')
          styleTag.id = 'allure-role-controller-style'
          styleTag.innerHTML = `
            .role-business .side-nav__item[data-ga4-param-tab="suites"],
            .role-business .side-nav__item[data-ga4-param-tab="packages"],
            .role-business .side-nav__item[data-ga4-param-tab="timeline"],
            .role-business .side-nav__item:has(a[href="#suites"]),
            .role-business .side-nav__item:has(a[href="#packages"]),
            .role-business .side-nav__item:has(a[href="#timeline"]),
            .role-business .side-nav__item:has(a[href*="suites"]),
            .role-business .side-nav__item:has(a[href*="packages"]),
            .role-business .side-nav__item:has(a[href*="timeline"]),
            .role-business a.side-nav__link[href="#suites"],
            .role-business a.side-nav__link[href="#packages"],
            .role-business a.side-nav__link[href="#timeline"] {
              display: none !important;
            }
          `
          doc.head.appendChild(styleTag)
        }
      }
    } catch (e) {
      // 容错处理
    }
  }
}

// 监听响应式角色变化，无论何时切换下拉框，均立刻执行同步
watch(selectedRole, () => {
  syncReportRole()
})

function handleIframeLoad() {
  syncReportRole()
  // 多频次重试以覆盖 Allure 内部动态渲染完成的时刻
  setTimeout(syncReportRole, 200)
  setTimeout(syncReportRole, 600)
}

// ==================== 7. Web 回执模态表单管理 ====================

function addReceiptRow() {
  const conclusionIndex = receiptFields.value.findIndex(f => f.key === '验收测试结论')
  const newField = { key: '', val: '' }
  if (conclusionIndex !== -1) {
    receiptFields.value.splice(conclusionIndex, 0, newField)
  } else {
    receiptFields.value.push(newField)
  }
}

function addDeviceReceipt() {
  const deviceCount = receiptFields.value.filter(f => f.key.startsWith('设备')).length + 1
  const conclusionIndex = receiptFields.value.findIndex(f => f.key === '验收测试结论')
  const newField = { key: `设备${deviceCount}`, val: '' }
  if (conclusionIndex !== -1) {
    receiptFields.value.splice(conclusionIndex, 0, newField)
  } else {
    receiptFields.value.push(newField)
  }
}

function addUserReceipt() {
  const userCount = receiptFields.value.filter(f => f.key.startsWith('私聊用户')).length + 1
  const conclusionIndex = receiptFields.value.findIndex(f => f.key === '验收测试结论')
  const newField = { key: `私聊用户${userCount}`, val: '' }
  if (conclusionIndex !== -1) {
    receiptFields.value.splice(conclusionIndex, 0, newField)
  } else {
    receiptFields.value.push(newField)
  }
}

function removeReceiptRow(index) {
  receiptFields.value.splice(index, 1)
}

function saveReceiptData() {
  isReceiptVisible.value = false
  ElMessage.success("💾 验收测试回执配置已保存更新")
}

// ==================== 8. 拖拽逻辑 (PointerEvent 高性能版) ====================

function handlePointerDownH(e) {
  e.preventDefault()
  isResizingH.value = true
  document.body.style.cursor = 'ew-resize'
  
  const onPointerMove = (moveEvent) => {
    let width = moveEvent.clientX
    if (width < 280) width = 280
    if (width > window.innerWidth - 450) width = window.innerWidth - 450
    sidebarWidth.value = width
  }
  
  const onPointerUp = () => {
    isResizingH.value = false
    document.body.style.cursor = 'default'
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', onPointerUp)
  }
  
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
}

function handlePointerDownV(e) {
  e.preventDefault()
  isResizingV.value = true
  document.body.style.cursor = 'ns-resize'
  
  const consoleArea = document.querySelector('.console-area')
  const rect = consoleArea.getBoundingClientRect()
  
  const onPointerMove = (moveEvent) => {
    let height = moveEvent.clientY - rect.top
    if (height < 150) height = 150
    if (height > rect.height - 100) height = rect.height - 100
    reportHeight.value = height
  }
  
  const onPointerUp = () => {
    isResizingV.value = false
    document.body.style.cursor = 'default'
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', onPointerUp)
  }
  
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
}

function handlePointerDownParams(e) {
  e.preventDefault()
  isResizingParams.value = true
  document.body.style.cursor = 'ns-resize'
  
  const startY = e.clientY
  const startHeight = paramsPanelHeight.value
  
  const onPointerMove = (moveEvent) => {
    const deltaY = moveEvent.clientY - startY
    let height = startHeight - deltaY
    // 最小高度为 42px (折叠状态)，超过 60px 自动展开
    if (height < 42) height = 42
    if (height > 60 && isParamsCollapsed.value) {
      isParamsCollapsed.value = false
    }
    if (height > window.innerHeight - 200) height = window.innerHeight - 200
    paramsPanelHeight.value = height
  }
  
  const onPointerUp = () => {
    isResizingParams.value = false
    document.body.style.cursor = 'default'
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', onPointerUp)
  }
  
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
}

// 参数面板一键折叠 / 展开
function toggleParamsCollapse() {
  isParamsCollapsed.value = !isParamsCollapsed.value
  if (isParamsCollapsed.value) {
    savedParamsHeight.value = paramsPanelHeight.value
    paramsPanelHeight.value = 42
  } else {
    paramsPanelHeight.value = (savedParamsHeight.value && savedParamsHeight.value > 100) ? savedParamsHeight.value : 420
  }
}

// 终端自动吸底开关切换
function toggleAutoScroll() {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value && terminalScreenRef.value) {
    terminalScreenRef.value.scrollTop = terminalScreenRef.value.scrollHeight
  }
}

// 终端手动滚动时检测是否处于底部
function handleTerminalScroll() {
  if (!terminalScreenRef.value) return
  const { scrollTop, scrollHeight, clientHeight } = terminalScreenRef.value
  const isAtBottom = scrollHeight - scrollTop - clientHeight < 30
  if (isAtBottom && !autoScroll.value) {
    autoScroll.value = true
  } else if (!isAtBottom && autoScroll.value) {
    autoScroll.value = false
  }
}

// 一键复制干净的终端日志
async function copyLogs() {
  try {
    const cleanText = stripAnsi(logsBuffer.value)
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(cleanText)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = cleanText
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    ElMessage.success("📋 已复制终端日志到剪贴板")
  } catch (e) {
    ElMessage.error("复制失败: " + e.message)
  }
}

function resetParams() {
  remoteAppium.value = '127.0.0.1:4723'
  remoteAppium2.value = '127.0.0.1:4724'
  remoteUdid.value = 'QFF0219A11009305'
  remoteUdid2.value = '20a5fa17'
  privateChatName.value = ''
  groupChatName.value = ''
  debugMode.value = false
  selectedRole.value = 'business'
  ElMessage.info("参数配置已重置为默认值")
}

function clearTerminal() {
  logsBuffer.value = '终端清空，等待选择用例运行...'
}

function updateNodeStatus(nodes, targetNodeId, status) {
  for (let node of nodes) {
    if ((node.isTest || node.isTestParam) && node.nodeid === targetNodeId) {
      node.status = status
      return true
    }
    if (node.children && node.children.length > 0) {
      const found = updateNodeStatus(node.children, targetNodeId, status)
      if (found) return true
    }
  }
  return false
}

function resetAllNodesStatus(nodes) {
  nodes.forEach(node => {
    if (node.isTest || node.isTestParam) {
      node.status = ''
    }
    if (node.children && node.children.length > 0) {
      resetAllNodesStatus(node.children)
    }
  })
}
</script>

<template>
  <div class="app-layout" :class="{ 'is-resizing': isResizingH || isResizingV || isResizingParams }">
    <!-- 主操作界面 -->
    <main class="app-main">
      <!-- 左边栏：包含用例搜索、用例树与调试参数 -->
      <section class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <div class="search-box">
          <el-input
            v-model="filterText"
            placeholder="输入关键字模糊搜索用例..."
            prefix-icon="Search"
            clearable
            class="search-input"
          />
          <div class="tree-tools">
            <el-button size="small" link type="primary" @click="toggleExpandAll(true)">展开</el-button>
            <span class="tool-divider">/</span>
            <el-button size="small" link type="info" @click="toggleExpandAll(false)">折叠</el-button>
          </div>
        </div>

        <!-- 用例树状展示（完全复刻 index.html 格式与图标） -->
        <div class="tree-container">
          <el-tree
            ref="treeRef"
            :data="catalog"
            node-key="id"
            :default-expanded-keys="defaultExpandedKeys"
            :filter-node-method="filterNode"
            :expand-on-click-node="true"
            @node-expand="handleNodeExpand"
            class="custom-tree"
          >
            <template #default="{ node, data }">
              <div class="tree-custom-node">
                <!-- 1. Category 目录分类节点 -->
                <div v-if="data.isCategory" class="test-item-row">
                  <span class="node-label">
                    {{ node.expanded ? '📖' : '📇' }} {{ data.label }} [{{ data.count }}]
                  </span>
                  <div class="test-item-actions" @click.stop>
                    <el-button
                      type="warning"
                      size="small"
                      plain
                      :disabled="isRunning"
                      @click="startTestExecution(data)"
                    >
                      运行目录
                    </el-button>
                  </div>
                </div>

                <!-- 2. File 测试文件节点 -->
                <div v-else-if="data.isFile" class="test-item-row">
                  <span class="node-label" :title="data.file">
                    👾 {{ data.label }} [{{ data.count }}]
                  </span>
                  <div class="test-item-actions" @click.stop>
                    <el-button
                      type="success"
                      size="small"
                      plain
                      :disabled="isRunning"
                      @click="startTestExecution(data)"
                    >
                      运行文件
                    </el-button>
                  </div>
                </div>

                <!-- 3. Class 测试类节点 -->
                <div v-else-if="data.isClass" class="test-item-row">
                  <span class="node-label">🧱 {{ data.label }}</span>
                  <div class="test-item-actions" @click.stop>
                    <el-button
                      type="warning"
                      size="small"
                      plain
                      :disabled="isRunning"
                      @click="startTestExecution(data)"
                    >
                      运行类
                    </el-button>
                  </div>
                </div>

                <!-- 4. TestGroup 参数化整个函数组 -->
                <div v-else-if="data.isTestGroup" class="test-item-row">
                  <span class="node-label">
                    👻 {{ data.label }} [{{ data.count }}] {{ node.expanded ? '' : '(已折叠)' }}
                  </span>
                  <div class="test-item-actions" @click.stop>
                    <el-button
                      type="primary"
                      size="small"
                      plain
                      :disabled="isRunning"
                      @click="startTestExecution(data)"
                    >
                      全组运行
                    </el-button>
                  </div>
                </div>

                <!-- 5. TestParam 参数化单个参数项 -->
                <div v-else-if="data.isTestParam" class="test-item-row">
                  <span class="status-radio-dot" :class="data.status || 'pending'"></span>
                  <span class="node-label" style="font-size: 12px; color: #94a3b8; padding-left: 6px;">
                    🚀 [{{ data.label }}]
                  </span>
                  <div class="test-item-actions" @click.stop>
                    <el-button
                      type="primary"
                      size="small"
                      plain
                      :disabled="isRunning"
                      @click="startTestExecution(data)"
                    >
                      运行
                    </el-button>
                  </div>
                </div>

                <!-- 6. 普通独立 Test 用例 -->
                <div v-else-if="data.isTest" class="test-item-row">
                  <span class="status-radio-dot" :class="data.status || 'pending'"></span>
                  <span class="node-label">⚙️ {{ data.label }}</span>
                  <div class="test-item-actions" @click.stop>
                    <el-button
                      type="primary"
                      size="small"
                      plain
                      :disabled="isRunning"
                      @click="startTestExecution(data)"
                    >
                      运行
                    </el-button>
                  </div>
                </div>
              </div>
            </template>
          </el-tree>
        </div>

        <!-- 参数拖拽调整分割线 -->
        <div class="resize-bar-params" @pointerdown="handlePointerDownParams"></div>

        <!-- 参数配置区 -->
        <div class="params-panel" :class="{ 'is-collapsed': isParamsCollapsed }" :style="{ height: paramsPanelHeight + 'px' }">
          <div class="panel-header" @click="toggleParamsCollapse">
            <div class="header-title">
              <span class="collapse-arrow" :class="{ 'collapsed': isParamsCollapsed }">▾</span>
              <span>🔌 远程调试与参数配置</span>
            </div>
            <div class="header-actions" @click.stop>
              <el-button link type="info" :disabled="isRunning" @click="resetParams">重置</el-button>
              <el-button link type="primary" @click="toggleParamsCollapse">
                {{ isParamsCollapsed ? '展开' : '收起' }}
              </el-button>
            </div>
          </div>

          <div v-show="!isParamsCollapsed" class="panel-body">
            <el-form label-position="top" size="small">
              <el-form-item>
                <template #label>
                  <div class="form-label-with-actions">
                    <span>Appium 1 地址 (发送端)</span>
                    <div class="label-actions">
                      <el-button class="label-btn label-btn-info" size="small" @click="triggerStartAppium(4723)">启动</el-button>
                      <el-button class="label-btn label-btn-primary" size="small" @click="detectAppiumStatus(4723)">探测</el-button>
                    </div>
                  </div>
                </template>
                <div class="appium-group">
                  <el-select v-model="osSelect" style="width: 100px; margin-right: 8px;" placeholder="系统">
                    <el-option label="Win" value="windows" />
                    <el-option label="Mac" value="mac" />
                  </el-select>
                  <el-select
                    v-model="remoteAppium"
                    filterable
                    allow-create
                    default-first-option
                    placeholder="选择或输入 Appium 地址"
                    style="flex: 1;"
                  >
                    <!-- <el-option label="127.0.0.1:4723 (本地)" value="127.0.0.1:4723" />
                    <el-option label="192.168.1.26:4723" value="192.168.1.26:4723" />
                    <el-option label="192.168.1.212:4723" value="192.168.1.212:4723" />
                    <el-option label="192.168.1.135:4723" value="192.168.1.135:4723" /> -->
                    <el-option
                      v-for="item in appium1Options"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </div>
              </el-form-item>

              <el-form-item>
                <template #label>
                  <div class="form-label-with-actions">
                    <span>Appium 2 地址 (接收端)</span>
                    <div class="label-actions">
                      <el-button class="label-btn label-btn-info" size="small" @click="triggerStartAppium(4724)">启动</el-button>
                      <el-button class="label-btn label-btn-primary" size="small" @click="detectAppiumStatus(4724)">探测</el-button>
                    </div>
                  </div>
                </template>
                <div class="appium-group">
                  <el-select
                    v-model="remoteAppium2"
                    filterable
                    allow-create
                    default-first-option
                    placeholder="选择或输入 Appium 2 地址"
                    style="width: 100%;"
                  >
                    <!-- <el-option label="127.0.0.1:4724 (本地)" value="127.0.0.1:4724" />
                    <el-option label="192.168.1.26:4724" value="192.168.1.26:4724" />
                    <el-option label="192.168.1.212:4724" value="192.168.1.212:4724" />
                    <el-option label="192.168.1.135:4724" value="192.168.1.135:4724" /> -->
                    <el-option
                      v-for="item in appium2Options"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </div>
              </el-form-item>

              <el-form-item>
                <template #label>
                  <div class="form-label-with-actions">
                    <span>第一部手机 UDID (发送端)</span>
                    <div class="label-actions">
                      <el-button class="label-btn label-btn-success" size="small" @click="detectConnectedDevices(1)">检测真机</el-button>
                    </div>
                  </div>
                </template>
                <div class="udid-group">
                  <el-select
                    v-model="remoteUdid"
                    filterable
                    allow-create
                    default-first-option
                    placeholder="自动检测、输入或选择UDID"
                    style="width: 100%;"
                  >
                    <el-option
                      v-for="item in deviceOptionList"
                      :key="'d1_' + item.udid"
                      :label="item.udid"
                      :value="item.udid"
                    >
                      <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                        <span style="font-family: monospace; font-size: 13px;">{{ item.udid }}</span>
                        <el-tag
                          size="small"
                          :type="item.is_real ? 'success' : (item.desc.includes('默认') ? 'warning' : 'info')"
                          effect="light"
                          style="margin-left: 12px;"
                        >
                          {{ item.desc }}
                        </el-tag>
                      </div>
                    </el-option>
                  </el-select>
                </div>
              </el-form-item>

              <div style="display: flex; justify-content: flex-end; margin-top: -6px; margin-bottom: 8px;">
                <el-button size="small" link type="primary" @click="swapDevices">
                  ⇅ 互换发送端与接收端手机
                </el-button>
              </div>

              <el-form-item>
                <template #label>
                  <div class="form-label-with-actions">
                    <span>第二部手机 UDID (接收端)</span>
                    <div class="label-actions">
                      <el-button class="label-btn label-btn-success" size="small" @click="detectConnectedDevices(2)">检测真机</el-button>
                    </div>
                  </div>
                </template>
                <div class="udid-group">
                  <el-select
                    v-model="remoteUdid2"
                    filterable
                    allow-create
                    default-first-option
                    placeholder="输入或选择第二部手机UDID"
                    style="width: 100%;"
                  >
                    <el-option
                      v-for="item in deviceOptionList"
                      :key="'d2_' + item.udid"
                      :label="item.udid"
                      :value="item.udid"
                    >
                      <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                        <span style="font-family: monospace; font-size: 13px;">{{ item.udid }}</span>
                        <el-tag
                          size="small"
                          :type="item.is_real ? 'success' : (item.desc.includes('默认') ? 'warning' : 'info')"
                          effect="light"
                          style="margin-left: 12px;"
                        >
                          {{ item.desc }}
                        </el-tag>
                      </div>
                    </el-option>
                  </el-select>
                </div>
              </el-form-item>

            <el-form-item label="业务调试变量 (私聊 / 群聊)">
              <div class="chat-vars-group">
                <el-select
                  v-model="privateChatName"
                  filterable
                  allow-create
                  default-first-option
                  placeholder="私聊测试名称"
                  style="flex: 1; margin-right: 8px;"
                >
                  <el-option label="test209-11" value="test209-11" />
                </el-select>
                <el-select
                  v-model="groupChatName"
                  filterable
                  allow-create
                  default-first-option
                  placeholder="群聊测试名称"
                  style="flex: 1;"
                >
                  <el-option label="测试aaaaa" value="测试aaaaa" />
                </el-select>
              </div>
            </el-form-item>

            <el-form-item>
              <el-checkbox v-model="debugMode">
                🐞 开启调试模式 (失败时保留 App 并拉起 PDB)
              </el-checkbox>
            </el-form-item>
          </el-form>
          </div>
        </div>
      </section>

      <!-- 左右分割拖拽条 -->
      <div class="h-resizer" @pointerdown="handlePointerDownH"></div>

      <!-- 右边栏：报告展示与实时日志 -->
      <section class="console-area">
        <!-- 上半部分: Allure 报告展示 -->
        <div class="report-container" :style="{ height: reportHeight + 'px' }">
          <div class="container-header">
            <div class="header-left">
              <span>📊 测试报告展示 (Allure 可视化面板)</span>
              <div class="status-badge" :class="globalStatus">
                <span class="status-dot"></span>
                <span>{{ globalStatusText }}</span>
              </div>
            </div>
            <div class="header-right">
              <el-button size="small" type="success" plain @click="isReceiptVisible = true">
                📝 填写 Web 回执
              </el-button>
              
              <el-select
                v-model="selectedRole"
                size="small"
                style="width: 160px; margin-left: 10px;"
                @change="syncReportRole"
              >
                <el-option label="精简视角" value="business" />
                <el-option label="完整视角" value="tech" />
              </el-select>

              <el-button size="small" type="primary" style="margin-left: 10px;" @click="refreshReport">
                刷新报告
              </el-button>
            </div>
          </div>

          <div class="iframe-wrapper">
            <iframe
              v-if="reportUrl"
              ref="iframeRef"
              :src="reportUrl"
              @load="handleIframeLoad"
            ></iframe>
            <div v-else class="iframe-placeholder">
              <div class="icon">✨</div>
              <div>测试报告引擎就绪</div>
              <div style="font-size: 11px; margin-top: 4px; color: var(--text-muted);">
                请先运行任意测试用例，报告生成后点击右上角“刷新报告”
              </div>
            </div>
          </div>
        </div>

        <!-- 上下分割拖拽条 -->
        <div class="v-resizer" @pointerdown="handlePointerDownV"></div>

        <!-- 下半部分: 终端日志 -->
        <div class="terminal-container">
          <div class="container-header">
            <div class="header-left">
              <span>📟 终端实时执行日志</span>
              <span v-if="runningCaseName" class="running-case-tip">
                正在执行: {{ runningCaseName }}
              </span>
            </div>
            <div class="header-right">
              <el-tooltip :content="autoScroll ? '已吸底，点击暂停自动滚屏' : '已暂停，点击恢复自动吸底'" placement="top">
                <el-button
                  size="small"
                  :type="autoScroll ? 'success' : 'info'"
                  plain
                  @click="toggleAutoScroll"
                >
                  {{ autoScroll ? '🟢 自动滚屏' : '⏸️ 滚屏暂停' }}
                </el-button>
              </el-tooltip>
              <el-button size="small" type="primary" plain @click="copyLogs">
                📋 复制日志
              </el-button>
              <el-button size="small" link type="info" @click="clearTerminal">清空终端</el-button>
              <el-button
                v-if="isRunning"
                size="small"
                type="danger"
                @click="stopCurrentTask"
              >
                终止运行
              </el-button>
            </div>
          </div>

          <pre
            ref="terminalScreenRef"
            class="terminal-screen"
            @scroll="handleTerminalScroll"
            v-html="formattedLogs"
          ></pre>
        </div>
      </section>
    </main>

    <!-- Web 回执配置弹窗 -->
    <el-dialog
      v-model="isReceiptVisible"
      title="📝 填写测试结果 Web 回执"
      width="500px"
      custom-class="custom-receipt-dialog"
      append-to-body
    >
      <p style="font-size: 12px; color: #909399; margin-bottom: 12px;">
        配置本次回归测试结束后自动生成的归档报告回执单内容（可用于通知非开发团队汇报）。
      </p>
      
      <div class="receipt-fields-list">
        <div v-for="(field, index) in receiptFields" :key="index" class="receipt-row">
          <el-input v-model="field.key" placeholder="项目" style="flex: 1; margin-right: 8px;" />
          <el-input v-model="field.val" placeholder="值..." style="flex: 2; margin-right: 8px;" />
          <el-button
            type="danger"
            icon="Delete"
            circle
            plain
            size="small"
            @click="removeReceiptRow(index)"
          />
        </div>
      </div>

      <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
        <el-button type="primary" plain size="small" icon="Plus" @click="addDeviceReceipt">
          添加测试设备
        </el-button>
        <el-button type="success" plain size="small" icon="Plus" @click="addUserReceipt">
          添加测试账号
        </el-button>
        <el-button type="info" plain size="small" icon="Plus" @click="addReceiptRow">
          增加普通项
        </el-button>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button size="small" @click="isReceiptVisible = false">取消</el-button>
          <el-button size="small" type="primary" @click="saveReceiptData">保存配置</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.app-layout {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 拖动大小时禁用整体选择 */
.app-layout.is-resizing {
  user-select: none !important;
  pointer-events: none !important;
}

/* ==================== 侧边栏头部 ==================== */
.sidebar-header {
  height: 56px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 16px;
  color: #fff;
}

.logo-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin: 0;
}

/* ==================== 主内容区 ==================== */
.app-main {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

/* 侧边栏 */
.sidebar {
  min-width: 280px;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  z-index: 5;
  overflow: hidden;
}

.search-box {
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--border-color);
}

.search-input {
  flex: 1;
}

.tree-tools {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.tool-divider {
  color: var(--text-muted, #94a3b8);
  font-size: 11px;
}

.tree-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.custom-tree {
  font-size: 13px;
}

:deep(.custom-tree .el-tree-node__content) {
  height: auto !important;
  padding: 6px 0;
}

.tree-custom-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  overflow: hidden;
}

.test-item-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
}

.node-label {
  min-width: 0;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  line-height: 1.5;
}

.test-item-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* 参数面板 */
.params-panel {
  padding: 0 16px 14px 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  border-top: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-sidebar-bottom, rgba(0, 0, 0, 0.015));
  transition: height 0.15s ease-out;
}

.params-panel.is-collapsed {
  padding-bottom: 0;
}

/* 参数拖拽调整分割线 */
.resize-bar-params {
  height: 6px;
  cursor: ns-resize;
  background: transparent;
  transition: background 0.3s;
  z-index: 10;
  position: relative;
  flex-shrink: 0;
}

.resize-bar-params:hover,
.app-layout.is-resizing .resize-bar-params {
  background: var(--el-color-primary-light-3, #409eff);
}

.panel-header {
  height: 42px;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.collapse-arrow {
  display: inline-block;
  transition: transform 0.2s ease;
  font-size: 12px;
}

.collapse-arrow.collapsed {
  transform: rotate(-90deg);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding-top: 4px;
}

.appium-group, .udid-group {
  display: flex;
  gap: 6px;
  width: 100%;
}

.chat-vars-group {
  display: flex;
  gap: 8px;
  width: 100%;
}

/* 分界线拖拽条 */
.h-resizer {
  width: 6px;
  cursor: ew-resize;
  background: transparent;
  transition: background 0.3s;
  z-index: 8;
  pointer-events: auto !important;
}
.h-resizer:hover, .app-layout.is-resizing .h-resizer {
  background: var(--primary-color);
}

.v-resizer {
  height: 6px;
  cursor: ns-resize;
  background: transparent;
  transition: background 0.3s;
  z-index: 8;
  pointer-events: auto !important;
}
.v-resizer:hover, .app-layout.is-resizing .v-resizer {
  background: var(--primary-color);
}

/* 右侧控制台区域 */
.console-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  pointer-events: auto !important;
}

/* 报告 */
.report-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.container-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 12px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #64748b;
}

.running .status-dot {
  background-color: var(--primary-color);
  box-shadow: 0 0 8px var(--primary-color);
  animation: blink 1.5s infinite;
}

.success .status-dot {
  background-color: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
}

.danger .status-dot {
  background-color: #f43f5e;
  box-shadow: 0 0 8px rgba(244, 63, 94, 0.4);
}

.iframe-wrapper {
  flex: 1;
  position: relative;
  height: 100%;
}

.iframe-wrapper iframe {
  width: 100%;
  height: 100%;
  border: none;
}

/* 防止拖拽过程中 iframe 吞噬鼠标/指针事件导致拖动卡顿、失效 */
.is-resizing iframe {
  pointer-events: none !important;
}

.iframe-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  text-align: center;
}

.iframe-placeholder .icon {
  font-size: 32px;
}

/* 终端 */
.terminal-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.running-case-tip {
  color: #94a3b8;
  font-size: 11px;
  font-weight: normal;
  margin-left: 10px;
}

.terminal-screen {
  flex: 1;
  margin: 0;
  padding: 16px 20px;
  font-family: var(--font-mono);
  font-size: 12.5px;
  line-height: 1.6;
  overflow-y: auto;
  white-space: pre-wrap;
}

/* 换页回执弹窗 */
.receipt-fields-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 260px;
  overflow-y: auto;
  padding-right: 4px;
}

.receipt-row {
  display: flex;
  align-items: center;
}

.form-label-with-actions {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  width: 100%;
}

.label-actions {
  display: flex;
  gap: 8px;
  margin-left: 16px; /* 增加与标题的横向间隔 */
}

/* 科技感药丸胶囊按钮美化 */
.label-btn {
  padding: 1px 8px !important;
  height: 18px !important;
  font-size: 10px !important;
  border-radius: 10px !important; /* 药丸弧度 */
  font-weight: 600 !important;
  border: none !important;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.label-btn-info {
  background: linear-gradient(135deg, #64748b, #475569) !important;
  color: #ffffff !important;
  box-shadow: 0 2px 5px rgba(100, 116, 139, 0.3) !important;
}
.label-btn-info:hover {
  background: linear-gradient(135deg, #78889b, #5a6a7f) !important;
  transform: translateY(-1px) scale(1.04) !important;
  box-shadow: 0 4px 10px rgba(100, 116, 139, 0.5) !important;
}

.label-btn-primary {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
  color: #ffffff !important;
  box-shadow: 0 2px 5px rgba(59, 130, 246, 0.35) !important;
}
.label-btn-primary:hover {
  background: linear-gradient(135deg, #60a5fa, #2563eb) !important;
  transform: translateY(-1px) scale(1.04) !important;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.55) !important;
}

.label-btn-success {
  background: linear-gradient(135deg, #10b981, #047857) !important;
  color: #ffffff !important;
  box-shadow: 0 2px 5px rgba(16, 185, 129, 0.35) !important;
}
.label-btn-success:hover {
  background: linear-gradient(135deg, #34d399, #059669) !important;
  transform: translateY(-1px) scale(1.04) !important;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.55) !important;
}

@keyframes blink {
  0% { opacity: 0.5; }
  50% { opacity: 1; }
  100% { opacity: 0.5; }
}

/* 用例状态圆点标识（类似 radio 效果） */
.status-radio-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #94a3b8; /* 默认灰色 */
  margin-right: 8px;
  background-color: transparent;
  box-sizing: border-box;
  vertical-align: middle;
  flex-shrink: 0;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.status-radio-dot.pending {
  border-color: #94a3b8;
  background-color: transparent;
}

.status-radio-dot.passed {
  border-color: #10b981; /* 绿色 */
  background-color: #10b981;
  box-shadow: 0 0 5px rgba(16, 185, 129, 0.6);
}

.status-radio-dot.failed {
  border-color: #ef4444; /* 红色 */
  background-color: #ef4444;
  box-shadow: 0 0 5px rgba(239, 68, 68, 0.6);
}

.status-radio-dot.skipped {
  border-color: #f97316; /* 橙色 */
  background-color: #f97316;
  box-shadow: 0 0 5px rgba(249, 115, 22, 0.6);
}
</style>
