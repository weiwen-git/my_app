import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, setUser } from './auth.js'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('./views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('./layout/AdminLayout.vue'),
    children: [
      { path: '', redirect: '/worklist' },
      {
        path: 'worklist',
        name: 'worklist',
        component: () => import('./views/WorkList.vue'),
        meta: { title: '工作清单', menu: 'worklist' }
      },
      {
        path: 'worklist/templates',
        name: 'templates',
        component: () => import('./views/TemplateManage.vue'),
        meta: { title: '模板管理', menu: 'worklist' }
      },
      {
        path: 'data',
        name: 'data-overview',
        component: () => import('./views/SheetOverview.vue'),
        meta: { title: '数据', menu: 'data' }
      },
      {
        path: 'data/:sheetId',
        name: 'data-sheet',
        component: () => import('./views/DataSheet.vue'),
        meta: { title: '数据表', menu: 'data' }
      },
      {
        path: 'todos',
        name: 'todos',
        component: () => import('./views/TodoList.vue'),
        meta: { title: '待办', menu: 'todos' }
      },
      {
        path: 'sticky',
        name: 'sticky',
        component: () => import('./views/StickyBoard.vue'),
        meta: { title: '便签', menu: 'sticky' }
      },
      {
        path: 'notes',
        name: 'notes',
        component: () => import('./views/NoteList.vue'),
        meta: { title: '笔记', menu: 'notes' }
      },
      {
        path: 'translate',
        name: 'translate',
        component: () => import('./views/Translate.vue'),
        meta: { title: '翻译', menu: 'translate' }
      }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/worklist' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 用原生 fetch 探测登录态：不走统一请求封装，避免失败时触发二次跳转
async function probeSession() {
  try {
    const res = await fetch('/api/auth/me', { credentials: 'include' })
    if (!res.ok) return false
    const payload = await res.json()
    if (payload?.ok) {
      setUser(payload.data)
      return true
    }
    return false
  } catch {
    return false
  }
}

router.beforeEach(async (to) => {
  if (to.meta.public) {
    if (isLoggedIn()) return { path: '/worklist' }
    return true
  }

  if (isLoggedIn()) return true

  const valid = await probeSession()
  if (valid) return true

  return { path: '/login', query: { redirect: to.fullPath } }
})

export default router
