import { clearUser, setUser } from './auth.js'

export class ApiError extends Error {
  constructor(message, code, status) {
    super(message)
    this.name = 'ApiError'
    this.code = code || 'unknown'
    this.status = status || 0
  }
}

function buildUrl(path, query) {
  if (!query) return path
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(query)) {
    if (v !== undefined && v !== null && v !== '') qs.append(k, v)
  }
  const s = qs.toString()
  return s ? `${path}?${s}` : path
}

async function request(path, { method = 'GET', body, query } = {}) {
  let res
  try {
    res = await fetch(buildUrl(path, query), {
      method,
      credentials: 'include',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body === undefined ? undefined : JSON.stringify(body)
    })
  } catch (err) {
    throw new ApiError('无法连接服务器，请检查后端是否启动', 'network_error', 0)
  }

  // 统一处理登录失效：清状态并跳登录，避免页面白屏
  if (res.status === 401) {
    clearUser()
    if (!location.pathname.startsWith('/login')) {
      location.replace('/login')
    }
    throw new ApiError('登录已失效，请重新登录', 'unauthorized', 401)
  }

  const payload = await res.json().catch(() => null)
  if (!res.ok || !payload || payload.ok !== true) {
    const msg = payload?.error?.message || `请求失败（${res.status}）`
    throw new ApiError(msg, payload?.error?.code, res.status)
  }
  return payload.data
}

export const api = {
  health: () => request('/api/health'),

  auth: {
    login: (username, password) => request('/api/auth/login', { method: 'POST', body: { username, password } }),
    logout: () => request('/api/auth/logout', { method: 'POST' }),
    me: () => request('/api/auth/me')
  },

  shops: {
    list: (includeInactive = false) => request('/api/shops', { query: { include_inactive: includeInactive } }),
    create: (payload) => request('/api/shops', { method: 'POST', body: payload }),
    update: (id, payload) => request(`/api/shops/${id}`, { method: 'PATCH', body: payload })
  },

  tasks: {
    generate: (date) => request('/api/tasks/generate', { method: 'POST', query: { date } }),
    list: ({ date, shopId = 'all', period = 'daily' } = {}) =>
      request('/api/tasks', { query: { date, shop_id: shopId, period } }),
    toggle: (id) => request(`/api/tasks/${id}/toggle`, { method: 'PATCH' }),
    remove: (id) => request(`/api/tasks/${id}`, { method: 'DELETE' }),
    abandon: (id) => request(`/api/tasks/${id}/abandon`, { method: 'POST' })
  },

  templates: {
    list: (shopId = 'all') => request('/api/templates/list', { query: { shop_id: shopId } }),
    create: (payload) => request('/api/templates', { method: 'POST', body: payload }),
    update: (id, payload) => request(`/api/templates/${id}`, { method: 'PATCH', body: payload })
  },

  sheets: {
    list: () => request('/api/sheets'),
    create: (name) => request('/api/sheets', { method: 'POST', body: { name } }),
    get: (id) => request(`/api/sheets/${id}`),
    rename: (id, name) => request(`/api/sheets/${id}`, { method: 'PATCH', body: { name } }),
    remove: (id) => request(`/api/sheets/${id}`, { method: 'DELETE' }),

    addColumn: (sheetId, payload) => request(`/api/sheets/${sheetId}/columns`, { method: 'POST', body: payload }),
    updateColumn: (sheetId, colId, payload) =>
      request(`/api/sheets/${sheetId}/columns/${colId}`, { method: 'PATCH', body: payload }),
    removeColumn: (sheetId, colId) => request(`/api/sheets/${sheetId}/columns/${colId}`, { method: 'DELETE' }),

    addRow: (sheetId, values) => request(`/api/sheets/${sheetId}/rows`, { method: 'POST', body: { values } }),
    updateRow: (sheetId, rowId, values) =>
      request(`/api/sheets/${sheetId}/rows/${rowId}`, { method: 'PATCH', body: { values } }),
    removeRow: (sheetId, rowId) => request(`/api/sheets/${sheetId}/rows/${rowId}`, { method: 'DELETE' }),

    importCsv: (sheetId, text) => request(`/api/sheets/${sheetId}/import`, { method: 'POST', body: { text } })
  },

  todos: {
    list: () => request('/api/todos'),
    create: (payload) => request('/api/todos', { method: 'POST', body: payload }),
    update: (id, payload) => request(`/api/todos/${id}`, { method: 'PATCH', body: payload }),
    remove: (id) => request(`/api/todos/${id}`, { method: 'DELETE' })
  },

  sticky: {
    list: () => request('/api/sticky'),
    create: (payload) => request('/api/sticky', { method: 'POST', body: payload }),
    update: (id, payload) => request(`/api/sticky/${id}`, { method: 'PATCH', body: payload }),
    remove: (id) => request(`/api/sticky/${id}`, { method: 'DELETE' })
  },

  notes: {
    list: (q = '') => request('/api/notes', { query: { q } }),
    get: (id) => request(`/api/notes/${id}`),
    create: (payload) => request('/api/notes', { method: 'POST', body: payload }),
    update: (id, payload) => request(`/api/notes/${id}`, { method: 'PATCH', body: payload }),
    remove: (id) => request(`/api/notes/${id}`, { method: 'DELETE' })
  }
}

// 登录成功后同步一次用户信息，供路由守卫与顶栏使用
export async function bootstrapSession() {
  const me = await api.auth.me()
  setUser(me)
  return me
}
