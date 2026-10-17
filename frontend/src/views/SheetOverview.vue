<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">数据</h2>
        <span class="page-sub">{{ sheets.length }} 张表</span>
      </div>
      <el-button type="primary" size="small" @click="openCreate">+ 新建数据表</el-button>
    </div>

    <div class="card-block" style="flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden">
      <el-table
        v-loading="loading"
        :data="sheets"
        style="width: 100%"
        size="small"
        @row-click="enterSheet"
      >
        <el-table-column prop="name" label="表名" min-width="160">
          <template #default="{ row }">
            <span class="sheet-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="column_count" label="列数" width="80" align="right" />
        <el-table-column prop="row_count" label="记录数" width="90" align="right" />
        <el-table-column prop="updated_at" label="最近更新" width="170">
          <template #default="{ row }">
            <span class="muted">{{ row.updated_at || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" align="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="enterSheet(row)">进入</el-button>
            <el-button link type="danger" size="small" @click.stop="removeSheet(row)">删除</el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="还没有数据表" :image-size="70" />
        </template>
      </el-table>
    </div>

    <el-dialog v-model="createVisible" title="新建数据表" width="360px">
      <el-input v-model="newName" placeholder="如：ICBU 周数据" maxlength="40" @keyup.enter="create" />
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="create">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api.js'

const router = useRouter()
const sheets = ref([])
const loading = ref(false)
const createVisible = ref(false)
const newName = ref('')
const creating = ref(false)

async function load() {
  loading.value = true
  try {
    sheets.value = await api.sheets.list()
  } catch (err) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function enterSheet(row) {
  router.push(`/data/${row.id}`)
}

function openCreate() {
  newName.value = ''
  createVisible.value = true
}

async function create() {
  const name = newName.value.trim()
  if (!name) {
    ElMessage.warning('请输入表名')
    return
  }
  creating.value = true
  try {
    const sheet = await api.sheets.create(name)
    createVisible.value = false
    ElMessage.success('已创建')
    await load()
    router.push(`/data/${sheet.id}`)
  } catch (err) {
    ElMessage.error(err.message || '创建失败')
  } finally {
    creating.value = false
  }
}

async function removeSheet(row) {
  try {
    await ElMessageBox.confirm(`删除数据表「${row.name}」？该表所有记录会一并失效。`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await api.sheets.remove(row.id)
    ElMessage.success('已删除')
    await load()
  } catch (err) {
    ElMessage.error(err.message || '删除失败')
  }
}

onMounted(load)
</script>

<style scoped>
.header-left {
  display: flex;
  align-items: baseline;
}

.sheet-name {
  color: #303133;
  cursor: pointer;
}

.muted {
  color: #909399;
}

:deep(.el-table__row) {
  cursor: pointer;
}
</style>
