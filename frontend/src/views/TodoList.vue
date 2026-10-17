<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">待办</h2>
        <span class="page-sub">临时接到的、不属于店铺的事 · 未完成 {{ todoList.length }}</span>
      </div>
      <el-button type="primary" size="small" @click="openCreate">+ 新增待办</el-button>
    </div>

    <div v-loading="loading" class="card-block list-card">
      <div class="scroll-y list-body">
        <div v-for="item in todoList" :key="item.id" class="todo-row">
          <el-checkbox :model-value="false" @change="toggle(item)" />
          <div class="todo-main">
            <div class="todo-title">{{ item.title }}</div>
            <div v-if="item.note" class="todo-note">{{ item.note }}</div>
          </div>
          <el-tag size="small" :type="priorityType(item.priority)" effect="plain">
            {{ priorityText(item.priority) }}
          </el-tag>
          <span class="due" :class="dueInfo(item.due_date).cls">{{ dueInfo(item.due_date).text }}</span>
          <el-button link type="primary" size="small" @click="openEdit(item)">编辑</el-button>
          <el-button link size="small" class="del-btn" @click="remove(item)">删除</el-button>
        </div>

        <el-empty v-if="!loading && todoList.length === 0" description="没有待办，清爽" :image-size="60" />
      </div>

      <div class="done-bar" @click="showDone = !showDone">
        <span>已完成 {{ doneList.length }} 项</span>
        <span>{{ showDone ? '▾' : '▸' }}</span>
      </div>

      <div v-if="showDone" class="scroll-y done-body">
        <div v-for="item in doneList" :key="item.id" class="todo-row done-row">
          <el-checkbox :model-value="true" @change="toggle(item)" />
          <div class="todo-main">
            <div class="todo-title done-text">{{ item.title }}</div>
          </div>
          <span class="due muted">{{ (item.done_at || '').slice(0, 16) }} 完成</span>
          <el-button link size="small" class="del-btn" @click="remove(item)">删除</el-button>
        </div>
        <el-empty v-if="doneList.length === 0" description="还没有完成的待办" :image-size="50" />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑待办' : '新增待办'" width="420px">
      <el-form :model="form" label-width="70px">
        <el-form-item label="内容" required>
          <el-input v-model="form.title" placeholder="要做什么" maxlength="120" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="2" maxlength="2000" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority">
            <el-radio-button label="high">高</el-radio-button>
            <el-radio-button label="normal">普通</el-radio-button>
            <el-radio-button label="low">低</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="截止日">
          <el-date-picker
            v-model="form.due_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="可不填"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api.js'

const todoList = ref([])
const doneList = ref([])
const loading = ref(false)
const showDone = ref(false)

const dialogVisible = ref(false)
const editing = ref(null)
const saving = ref(false)

const form = reactive({ title: '', note: '', priority: 'normal', due_date: null })

const priorityType = (p) => ({ high: 'danger', normal: 'primary', low: 'info' }[p] || 'info')
const priorityText = (p) => ({ high: '高', normal: '普通', low: '低' }[p] || '普通')

function todayStr() {
  const now = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  const p = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())}`
}

function dueInfo(date) {
  if (!date) return { text: '无截止', cls: 'muted' }
  const today = new Date(todayStr() + 'T00:00:00')
  const target = new Date(date + 'T00:00:00')
  const diff = Math.round((target - today) / 86400000)
  if (diff < 0) return { text: `${date} 已过期`, cls: 'overdue' }
  if (diff === 0) return { text: '今天截止', cls: 'urgent' }
  if (diff === 1) return { text: '明天截止', cls: 'urgent' }
  return { text: `${date} 截止`, cls: 'normal-due' }
}

async function load() {
  loading.value = true
  try {
    const data = await api.todos.list()
    todoList.value = data.todo
    doneList.value = data.done
  } catch (err) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.title = ''
  form.note = ''
  form.priority = 'normal'
  form.due_date = null
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  form.title = row.title
  form.note = row.note || ''
  form.priority = row.priority || 'normal'
  form.due_date = row.due_date || null
  dialogVisible.value = true
}

async function save() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写内容')
    return
  }
  saving.value = true
  try {
    const payload = {
      title: form.title.trim(),
      note: form.note.trim(),
      priority: form.priority,
      due_date: form.due_date || null
    }
    if (editing.value) {
      await api.todos.update(editing.value.id, payload)
      ElMessage.success('已保存')
    } else {
      await api.todos.create(payload)
      ElMessage.success('已添加')
    }
    dialogVisible.value = false
    await load()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggle(item) {
  try {
    await api.todos.update(item.id, { status: item.status === 'done' ? 'todo' : 'done' })
    await load()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  }
}

async function remove(item) {
  try {
    await ElMessageBox.confirm(`删除「${item.title}」？`, '确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await api.todos.remove(item.id)
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

.list-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 4px 12px;
}

.list-body {
  flex: 1;
  min-height: 0;
}

.todo-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 46px;
  padding: 5px 0;
  border-bottom: 1px solid #f5f7fa;
}

.todo-main {
  flex: 1;
  min-width: 0;
}

.todo-title {
  font-size: 14px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-note {
  font-size: 13px;
  color: #a8abb2;
  margin-top: 1px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.due {
  font-size: 13px;
  flex-shrink: 0;
  min-width: 82px;
  text-align: right;
}

.due.muted {
  color: #c0c4cc;
}

.due.urgent {
  color: #e6a23c;
}

.due.overdue {
  color: #d93025;
  font-weight: 500;
}

.due.normal-due {
  color: #909399;
}

.del-btn {
  color: #c0c4cc !important;
}

.done-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-top: 1px solid #ebeef5;
  font-size: 13px;
  color: #909399;
  cursor: pointer;
  flex-shrink: 0;
}

.done-body {
  max-height: 180px;
  flex-shrink: 0;
}

.done-row {
  opacity: 0.75;
}

.done-text {
  color: #c0c4cc;
  text-decoration: line-through;
}
</style>
