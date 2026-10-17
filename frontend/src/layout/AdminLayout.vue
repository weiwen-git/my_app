<template>
  <el-container class="app-shell">
    <el-aside width="200px" class="app-aside">
      <div class="brand">
        <div class="brand-mark"></div>
        <span class="brand-name">个人工作台</span>
      </div>

      <el-menu
        ref="menuRef"
        class="side-menu"
        :default-active="activePath"
        router
        unique-opened
      >
        <el-menu-item index="/worklist" @click="go('/worklist')">
          <span>工作清单</span>
        </el-menu-item>

        <el-sub-menu index="data">
          <template #title><span>数据</span></template>
          <el-menu-item index="/data" @click="go('/data')">全部数据表</el-menu-item>
          <el-menu-item
            v-for="sheet in sheets"
            :key="sheet.id"
            :index="`/data/${sheet.id}`"
            @click="go(`/data/${sheet.id}`)"
          >
            {{ sheet.name }}
          </el-menu-item>
          <el-menu-item index="__new_sheet" @click="openNewSheet">+ 新建数据表</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/todos" @click="go('/todos')">
          <span>待办</span>
        </el-menu-item>
        <el-menu-item index="/sticky" @click="go('/sticky')">
          <span>便签</span>
        </el-menu-item>
        <el-menu-item index="/notes" @click="go('/notes')">
          <span>笔记</span>
        </el-menu-item>
        <el-menu-item index="/translate" @click="go('/translate')">
          <span>翻译</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="app-body">
      <el-header height="56px" class="app-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/worklist' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ pageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-button link type="primary" @click="doLogout">退出</el-button>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>

    <el-dialog v-model="newSheetVisible" title="新建数据表" width="360px">
      <el-form @submit.prevent="createSheet">
        <el-form-item label="表名">
          <el-input v-model="newSheetName" placeholder="如：ICBU 周数据" maxlength="40" autofocus />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newSheetVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createSheet">创建</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { computed, nextTick, onMounted, provide, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api.js'
import { clearUser } from '../auth.js'

const route = useRoute()
const router = useRouter()

const sheets = ref([])
const menuRef = ref(null)
const newSheetVisible = ref(false)
const newSheetName = ref('')
const creating = ref(false)

const activePath = computed(() => route.path)

const pageTitle = computed(() => {
  // 具体数据表页显示表名，而不是笼统的「数据表」
  if (route.name === 'data-sheet') {
    const sheet = sheets.value.find((s) => String(s.id) === String(route.params.sheetId))
    return sheet?.name || '数据表'
  }
  return route.meta.title || '工作清单'
})

function go(path) {
  if (route.path !== path) router.push(path)
}

async function loadSheets() {
  try {
    sheets.value = await api.sheets.list()
    // 子项是异步加载的，default-openeds 在挂载时已算完，这里必须手动展开一次
    await nextTick()
    menuRef.value?.open('data')
  } catch (err) {
    ElMessage.error(err.message || '加载数据表失败')
  }
}

// 供子页面在改名/删除后刷新侧边栏与面包屑
provide('refreshNav', loadSheets)

function openNewSheet() {
  newSheetName.value = ''
  newSheetVisible.value = true
}

async function createSheet() {
  const name = newSheetName.value.trim()
  if (!name) {
    ElMessage.warning('请输入表名')
    return
  }
  creating.value = true
  try {
    const sheet = await api.sheets.create(name)
    ElMessage.success('已创建')
    newSheetVisible.value = false
    await loadSheets()
    router.push(`/data/${sheet.id}`)
  } catch (err) {
    ElMessage.error(err.message || '创建失败')
  } finally {
    creating.value = false
  }
}

async function doLogout() {
  try {
    await api.auth.logout()
  } catch {
    /* 忽略：本地状态照清 */
  }
  clearUser()
  router.replace('/login')
}

onMounted(loadSheets)

// 新建/删除数据表后刷新子菜单
watch(
  () => route.path,
  (path) => {
    if (path.startsWith('/data')) loadSheets()
  }
)
</script>

<style scoped>
.app-shell {
  height: 100%;
}

.app-aside {
  background: #304156;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.brand {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  background: #2b3a4a;
  flex-shrink: 0;
}

.brand-mark {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  background: #409eff;
}

.brand-name {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}

.side-menu {
  border-right: none;
  background: #304156;
  flex: 1;
  overflow-y: auto;
}

.side-menu :deep(.el-menu-item),
.side-menu :deep(.el-sub-menu__title) {
  color: #bfcbd9;
  height: 46px;
  line-height: 46px;
  font-size: 14px;
}

.side-menu :deep(.el-menu-item:hover),
.side-menu :deep(.el-sub-menu__title:hover) {
  background: #263445;
}

.side-menu :deep(.el-menu-item.is-active) {
  color: #409eff;
  background: #263445;
  border-left: 2px solid #409eff;
}

.side-menu :deep(.el-sub-menu .el-menu-item) {
  background: #2b3a4a;
  height: 40px;
  line-height: 40px;
  font-size: 13px;
  padding-left: 44px !important;
}

.side-menu :deep(.el-sub-menu .el-menu-item.is-active) {
  background: #263445;
}

.app-body {
  min-width: 0;
}

.app-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.header-title {
  font-size: 14px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-date {
  font-size: 13px;
  color: #909399;
}

.app-main {
  padding: 12px;
  overflow: hidden;
  background: #f0f2f5;
}
</style>
