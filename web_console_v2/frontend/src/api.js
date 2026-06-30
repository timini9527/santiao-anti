const jsonHeaders = { 'Content-Type': 'application/json' }

async function request(path, options = {}) {
  const response = await fetch(path, options)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = data.detail
    const message = typeof detail === 'string' ? detail : detail?.message || data.message || '请求失败'
    throw new Error(message)
  }
  return data
}

export function getHealth() {
  return request('/api/health')
}

export function getTests() {
  return request('/api/tests')
}

export function runTest(payload) {
  return request('/api/run', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(payload)
  })
}

export function stopTask(taskId) {
  return request(`/api/stop/${taskId}`, { method: 'POST' })
}

export function getTasks() {
  return request('/api/tasks')
}

export function getTaskStatus(taskId) {
  return request(`/api/status/${taskId}`)
}
