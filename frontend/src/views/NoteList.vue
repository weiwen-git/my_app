<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">笔记</h2>
        <span class="page-sub">{{ notes.length }} 篇</span>
      </div>
      <el-button type="primary" size="small" @click="createNote">+ 新建笔记</el-button>
    </div>

    <div class="note-layout">
      <div class="card-block note-list">
        <div class="search-wrap">
          <el-input v-model="keyword" size="small" placeholder="搜索标题" clearable />
        </div>
        <div class="list-scroll scroll-y">
          <div
            v-for="n in filtered"
            :key="n.id"
            class="note-item"
            :class="{ active: n.id === currentId }"
            @click="selectNote(n.id)"
          >
            <div class="note-item-title">{{ n.title || '未命名' }}</div>
            <div class="note-item-time">{{ (n.updated_at || '').slice(0, 16) }}</div>
          </div>
          <el-empty v-if="filtered.length === 0" description="没有笔记" :image-size="50" />
        </div>
      </div>

      <div v-loading="detailLoading" class="card-block note-editor">
        <template v-if="currentId">
          <div class="editor-head">
            <input v-model="form.title" class="title-input" placeholder="标题" @input="scheduleSave" />
            <el-button link type="danger" size="small" @click="deleteCurrent">删除</el-button>
          </div>
          <textarea
            v-model="form.content"
            class="content-input"
            placeholder="正文，纯文本，支持换行"
            @input="scheduleSave"
          ></textarea>
          <div class="editor-foot">
            <span class="save-state">{{ saveState }}</span>
            <span class="muted">{{ (form.updated_at || '').slice(0, 16) }}</span>
          </div>
        </template>
        <el-empty v-else description="选一篇笔记，或新建一篇" :image-size="70" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api.js'

const notes = ref([])
const currentId = ref(null)
const keyword = ref('')
const detailLoading = ref(false)
const saveState = ref('')

const form = reactive({ title: '', content: '', updated_at: '' })

let saveTimer = null

const filtered = computed(() => {
  const k = keyword.value.trim()
  if (!k) return notes.value
  return notes.value.filter((n) => (n.title || '').includes(k))
})

async function loadList(keepCurrent = true) {
  try {
    notes.value = await api.notes.list()
    if (!keepCurrent || !notes.value.some((n) => n.id === currentId.value)) {
      currentId.value = notes.value[0]?.id ?? null
    }
  } catch (err) {
    ElMessage.error(err.message || '加载失败')
  }
}

async function selectNote(id) {
  if (id === currentId.value) return
  await flushSave()
  currentId.value = id
}

watch(currentId, async (id) => {
  if (!id) {
    form.title = ''
    form.content = ''
    return
  }
  detailLoading.value = true
  try {
    const note = await api.notes.get(id)
    form.title = note.title
    form.content = note.content
    form.updated_at = note.updated_at
    saveState.value = ''
  } catch (err) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    detailLoading.value = false
  }
})

function scheduleSave() {
  saveState.value = '编辑中…'
  clearTimeout(saveTimer)
  saveTimer = setTimeout(flushSave, 1200)
}

async function flushSave() {
  clearTimeout(saveTimer)
  if (!currentId.value) return
  const snapshot = { title: form.title, content: form.content }
  try {
    const updated = await api.notes.update(currentId.value, snapshot)
    form.updated_at = updated.updated_at
    saveState.value = '已保存'
    const item = notes.value.find((n) => n.id === currentId.value)
    if (item) {
      item.title = updated.title
      item.updated_at = updated.updated_at
    }
  } catch (err) {
    saveState.value = '保存失败'
    ElMessage.error(err.message || '保存失败')
  }
}

async function createNote() {
  await flushSave()
  try {
    const note = await api.notes.create({ title: '未命名', content: '' })
    await loadList(false)
    currentId.value = note.id
    ElMessage.success('已新建')
  } catch (err) {
    ElMessage.error(err.message || '新建失败')
  }
}

async function deleteCurrent() {
  if (!currentId.value) return
  try {
    await ElMessageBox.confirm('删除这篇笔记？', '确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    clearTimeout(saveTimer)
    await api.notes.remove(currentId.value)
    currentId.value = null
    await loadList(false)
    ElMessage.success('已删除')
  } catch (err) {
    ElMessage.error(err.message || '删除失败')
  }
}

onMounted(() => loadList(false))
</script>

<style scoped>
.header-left {
  display: flex;
  align-items: baseline;
}

.note-layout {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 10px;
}

.note-list {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-wrap {
  padding: 8px;
  flex-shrink: 0;
}

.list-scroll {
  flex: 1;
  min-height: 0;
  border-top: 1px solid #f5f7fa;
}

.note-item {
  padding: 8px 10px;
  border-bottom: 1px solid #f5f7fa;
  cursor: pointer;
  border-left: 2px solid transparent;
}

.note-item:hover {
  background: #fafafa;
}

.note-item.active {
  background: #ecf5ff;
  border-left-color: #409eff;
}

.note-item-title {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note-item-time {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.note-editor {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 12px 14px;
  overflow: hidden;
}

.editor-head {
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
  flex-shrink: 0;
}

.title-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  font-family: inherit;
  background: transparent;
}

.content-input {
  flex: 1;
  min-height: 0;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.9;
  color: #606266;
  font-family: inherit;
  margin-top: 8px;
  background: transparent;
}

.editor-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid #f5f7fa;
  font-size: 13px;
  flex-shrink: 0;
}

.save-state {
  color: #67c23a;
}

.muted {
  color: #c0c4cc;
}
</style>
