<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">便签</h2>
        <span class="page-sub">{{ stickies.length }} 张</span>
      </div>
      <el-button type="primary" size="small" @click="createSticky">+ 新建便签</el-button>
    </div>

    <div v-loading="loading" class="board scroll-y">
      <div class="board-inner">
        <div
          v-for="item in stickies"
          :key="item.id"
          class="sticky"
          :class="`c-${item.color}`"
        >
          <div class="sticky-head">
            <span class="pin" :class="{ active: item.pinned }" title="置顶" @click="togglePin(item)">
              {{ item.pinned ? '★' : '☆' }}
            </span>
            <span class="tools">
              <span
                v-for="c in colors"
                :key="c"
                class="dot"
                :class="`d-${c}`"
                :title="colorLabel[c]"
                @click="changeColor(item, c)"
              ></span>
              <span class="close" title="删除" @click="removeSticky(item)">×</span>
            </span>
          </div>
          <textarea
            v-model="item.content"
            class="sticky-text"
            :ref="(el) => bindRef(item.id, el)"
            placeholder="写点什么…"
            @blur="saveSticky(item)"
          ></textarea>
        </div>

        <el-empty v-if="!loading && stickies.length === 0" description="还没有便签" :image-size="60" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api.js'

const stickies = ref([])
const loading = ref(false)
const refs = {}

const colors = ['yellow', 'blue', 'green', 'pink', 'gray']
const colorLabel = { yellow: '黄', blue: '蓝', green: '绿', pink: '粉', gray: '灰' }

function bindRef(id, el) {
  if (el) refs[id] = el
}

async function load() {
  loading.value = true
  try {
    stickies.value = await api.sticky.list()
  } catch (err) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function createSticky() {
  try {
    const created = await api.sticky.create({ content: '', color: 'yellow' })
    stickies.value.unshift(created)
    // 等 DOM 出来再聚焦，避免用户点了没反应
    setTimeout(() => refs[created.id]?.focus(), 50)
  } catch (err) {
    ElMessage.error(err.message || '创建失败')
  }
}

async function saveSticky(item) {
  try {
    const res = await api.sticky.update(item.id, { content: item.content })
    if (res.deleted) {
      stickies.value = stickies.value.filter((s) => s.id !== item.id)
      ElMessage.info('内容清空，便签已删除')
    }
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
    await load()
  }
}

async function changeColor(item, color) {
  try {
    await api.sticky.update(item.id, { color })
    item.color = color
  } catch (err) {
    ElMessage.error(err.message || '修改失败')
  }
}

async function togglePin(item) {
  try {
    await api.sticky.update(item.id, { pinned: item.pinned ? 0 : 1 })
    await load()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  }
}

async function removeSticky(item) {
  try {
    await ElMessageBox.confirm('删除这张便签？', '确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await api.sticky.remove(item.id)
    stickies.value = stickies.value.filter((s) => s.id !== item.id)
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

.board {
  flex: 1;
  min-height: 0;
}

.board-inner {
  column-count: 3;
  column-gap: 10px;
}

.sticky {
  break-inside: avoid;
  margin-bottom: 10px;
  border-radius: 4px;
  padding: 8px 10px 10px;
  border: 1px solid transparent;
}

.sticky.c-yellow {
  background: #fdf6ec;
  border-color: #faecd8;
}
.sticky.c-blue {
  background: #ecf5ff;
  border-color: #d9ecff;
}
.sticky.c-green {
  background: #f0f9eb;
  border-color: #e1f3d8;
}
.sticky.c-pink {
  background: #fef0f0;
  border-color: #fde2e2;
}
.sticky.c-gray {
  background: #f4f4f5;
  border-color: #e9e9eb;
}

.sticky-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  height: 16px;
}

.pin {
  cursor: pointer;
  font-size: 14px;
  color: #c0c4cc;
  line-height: 1;
}

.pin.active {
  color: #e6a23c;
}

.tools {
  display: flex;
  align-items: center;
  gap: 5px;
  opacity: 0;
  transition: opacity 0.15s;
}

.sticky:hover .tools {
  opacity: 1;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 2px;
  cursor: pointer;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.d-yellow {
  background: #f5d8a0;
}
.d-blue {
  background: #a8cdf0;
}
.d-green {
  background: #b3d8a0;
}
.d-pink {
  background: #f0b3b3;
}
.d-gray {
  background: #cfcfd4;
}

.close {
  cursor: pointer;
  color: #b9b9bd;
  font-size: 14px;
  line-height: 1;
}

.close:hover {
  color: #f56c6c;
}

.sticky-text {
  width: 100%;
  border: none;
  background: transparent;
  resize: none;
  outline: none;
  font-size: 14px;
  line-height: 1.7;
  color: #5c5c60;
  font-family: inherit;
  min-height: 52px;
  overflow: hidden;
}
</style>
