<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">{{ sheet?.name || '数据表' }}</h2>
        <span class="page-sub">{{ rows.length }} 条记录</span>
      </div>
      <div class="header-actions">
        <el-button size="small" @click="columnVisible = true">管理列</el-button>
        <el-button size="small" @click="csvVisible = true">粘贴 CSV</el-button>
        <el-button size="small" @click="renameSheet">改名</el-button>
        <el-button size="small" type="danger" plain @click="deleteSheet">删除表</el-button>
        <el-button type="primary" size="small" @click="openCreateRow">+ 新增记录</el-button>
      </div>
    </div>

    <div v-loading="loading" class="card-block table-wrap">
      <el-table
        :data="rows"
        size="small"
        height="100%"
        show-summary
        :summary-method="summaryMethod"
        :empty-text="columns.length ? '还没有记录' : '这张表还没有列，先点「管理列」加一列'"
      >
        <el-table-column
          v-for="col in sortedColumns"
          :key="col.id"
          :property="`c${col.id}`"
          :label="col.name"
          :min-width="col.type === 'text' ? 160 : 110"
          :align="col.type === 'number' ? 'right' : 'left'"
        >
          <template #default="{ row }">
            <span :class="{ muted: isBlank(row, col) }">{{ displayCell(row, col) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="110" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEditRow(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="removeRow(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-if="columns.length" class="summary-hint">
      合计规则：
      <span v-for="col in numberColumns" :key="col.id" class="hint-item">
        {{ col.name }} =
        {{ col.agg === 'sum' ? '求和' : col.agg === 'avg' ? '平均' : '不计' }}
      </span>
      <span v-if="numberColumns.length === 0" class="hint-item">当前没有数字列</span>
    </div>

    <ColumnManager
      v-model:visible="columnVisible"
      :sheet-id="sheetId"
      :columns="columns"
      @changed="load"
    />

    <RowEditor
      v-model:visible="rowVisible"
      :sheet-id="sheetId"
      :columns="columns"
      :row="editingRow"
      @changed="load"
    />

    <el-dialog v-model="csvVisible" title="粘贴 CSV" width="520px">
      <div class="csv-tip">
        按当前列顺序粘贴，逗号分隔。首行可以是表头（会自动跳过）。<br />
        当前列顺序：<b>{{ sortedColumns.map((c) => c.name).join(' , ') }}</b>
      </div>
      <el-input
        v-model="csvText"
        type="textarea"
        :rows="8"
        placeholder="2026-10-12,42,8240,316,3.2,本周有新客"
      />
      <template #footer>
        <el-button @click="csvVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api.js'
import ColumnManager from './components/ColumnManager.vue'
import RowEditor from './components/RowEditor.vue'

const route = useRoute()
const router = useRouter()
const refreshNav = inject('refreshNav', () => {})

const sheetId = computed(() => route.params.sheetId)
const sheet = ref(null)
const columns = ref([])
const rows = ref([])
const loading = ref(false)

const columnVisible = ref(false)
const rowVisible = ref(false)
const editingRow = ref(null)
const csvVisible = ref(false)
const csvText = ref('')
const importing = ref(false)

const sortedColumns = computed(() =>
  [...columns.value].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
)
const numberColumns = computed(() => sortedColumns.value.filter((c) => c.type === 'number'))

function isBlank(row, col) {
  const v = row.values?.[String(col.id)]
  return v === undefined || v === null || v === ''
}

function displayCell(row, col) {
  const v = row.values?.[String(col.id)]
  if (v === undefined || v === null || v === '') return '—'
  if (col.type === 'number') {
    const n = Number(v)
    if (!Number.isFinite(n)) return String(v)
    return Math.abs(n) >= 1000 ? n.toLocaleString('zh-CN', { maximumFractionDigits: 2 }) : String(n)
  }
  return String(v)
}

function columnTotal(col) {
  if (col.type !== 'number' || col.agg === 'none') return null
  const nums = rows.value
    .map((r) => Number(r.values?.[String(col.id)]))
    .filter((n) => Number.isFinite(n))
  if (nums.length === 0) return null
  const sum = nums.reduce((a, b) => a + b, 0)
  return col.agg === 'avg' ? sum / nums.length : sum
}

function summaryMethod({ columns: tableCols }) {
  return tableCols.map((tc, index) => {
    if (index === 0) return '合计 / 均值'
    if (!tc.property) return ''
    const colId = tc.property.slice(1)
    const col = sortedColumns.value.find((c) => String(c.id) === colId)
    if (!col) return ''
    const total = columnTotal(col)
    if (total === null) return ''
    const rounded = Number(total.toFixed(2))
    return Math.abs(rounded) >= 1000
      ? rounded.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
      : String(rounded)
  })
}

async function load() {
  loading.value = true
  try {
    const data = await api.sheets.get(sheetId.value)
    sheet.value = data.sheet
    columns.value = data.columns
    rows.value = data.rows
  } catch (err) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function openCreateRow() {
  if (columns.value.length === 0) {
    ElMessage.warning('先点「管理列」加一列')
    return
  }
  editingRow.value = null
  rowVisible.value = true
}

function openEditRow(row) {
  editingRow.value = row
  rowVisible.value = true
}

async function removeRow(row) {
  try {
    await ElMessageBox.confirm('删除这条记录？', '确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await api.sheets.removeRow(sheetId.value, row.id)
    await load()
  } catch (err) {
    ElMessage.error(err.message || '删除失败')
  }
}

async function doImport() {
  if (!csvText.value.trim()) {
    ElMessage.warning('先粘贴内容')
    return
  }
  importing.value = true
  try {
    const res = await api.sheets.importCsv(sheetId.value, csvText.value)
    ElMessage.success(`已导入 ${res.imported} 行`)
    csvVisible.value = false
    csvText.value = ''
    await load()
  } catch (err) {
    ElMessage.error(err.message || '导入失败')
  } finally {
    importing.value = false
  }
}

async function renameSheet() {
  let value
  try {
    const res = await ElMessageBox.prompt('新的表名', '改名', {
      inputValue: sheet.value?.name || '',
      confirmButtonText: '保存',
      cancelButtonText: '取消'
    })
    value = res.value?.trim()
  } catch {
    return
  }
  if (!value) return
  try {
    await api.sheets.rename(sheetId.value, value)
    ElMessage.success('已改名')
    await load()
    await refreshNav() // 侧边栏与面包屑同步新名字
  } catch (err) {
    ElMessage.error(err.message || '改名失败')
  }
}

async function deleteSheet() {
  try {
    await ElMessageBox.confirm(
      `删除数据表「${sheet.value?.name}」？该表所有记录会一并失效。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await api.sheets.remove(sheetId.value)
    ElMessage.success('已删除')
    router.replace('/data')
  } catch (err) {
    ElMessage.error(err.message || '删除失败')
  }
}

onMounted(load)
watch(() => route.params.sheetId, load)
</script>

<style scoped>
.header-left {
  display: flex;
  align-items: baseline;
}

.header-actions {
  display: flex;
  gap: 6px;
}

.table-wrap {
  flex: 1;
  min-height: 0;
  padding: 4px;
}

.muted {
  color: #c0c4cc;
}

.summary-hint {
  font-size: 13px;
  color: #909399;
  flex-shrink: 0;
}

.hint-item {
  margin-right: 12px;
}

.csv-tip {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.7;
}
</style>
