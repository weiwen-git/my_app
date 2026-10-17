<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">工作清单</h2>
        <span class="page-sub">{{ todayText }}</span>
      </div>
      <el-button size="small" @click="$router.push('/worklist/templates')">管理模板</el-button>
    </div>

    <!-- 店铺切页 -->
    <div class="shop-tabs">
      <el-button
        v-for="tab in shopTabs"
        :key="tab.value"
        size="small"
        :type="shopId === tab.value ? 'primary' : 'default'"
        @click="switchShop(tab.value)"
      >
        {{ tab.label }}
      </el-button>
      <el-button size="small" :icon="Setting" circle title="管理店铺" @click="openShopDialog" />
    </div>

    <!-- 空态引导 -->
    <div v-if="!loading && shops.length === 0" class="card-block empty-guide">
      <el-empty description="还没有配置店铺和工作清单" :image-size="80">
        <div class="guide-steps">
          <div class="guide-step"><b>1</b> 添加你的店铺</div>
          <div class="guide-step"><b>2</b> 为每个店铺建工作清单模板</div>
          <div class="guide-step"><b>3</b> 明天开始自动出现在这里</div>
        </div>
        <div class="guide-actions">
          <el-button type="primary" @click="openShopDialog">添加店铺</el-button>
          <el-button @click="$router.push('/worklist/templates')">建模板</el-button>
        </div>
      </el-empty>
    </div>

    <!-- 清单主体 -->
    <div v-else v-loading="loading" class="card-block list-card">
      <div class="period-tabs">
        <div
          v-for="p in periodTabs"
          :key="p.value"
          class="period-tab"
          :class="{ active: period === p.value }"
          @click="switchPeriod(p.value)"
        >
          <span>{{ p.label }}</span>
          <span v-if="counts[p.value]" class="badge" :class="{ 'badge-active': period === p.value }">
            {{ counts[p.value] }}
          </span>
        </div>
      </div>

      <div class="list-body scroll-y">
        <!-- 逾期区：有内容时常驻展开 -->
        <div v-if="overdue.length" class="overdue-box">
          <div class="overdue-title">逾期 {{ overdue.length }} 项（已顺延满 7 天）</div>
          <div v-for="item in overdue" :key="item.id" class="task-row overdue-row">
            <el-checkbox :model-value="false" @change="toggle(item)" />
            <span class="task-title overdue-text">{{ item.title }}</span>
            <span class="overdue-days">逾期 {{ item.carried }} 天</span>
            <el-button link type="primary" size="small" @click="toggle(item)">完成</el-button>
            <el-button link size="small" @click="abandon(item)">放弃</el-button>
          </div>
        </div>

        <!-- 全部店铺：按店分组 -->
        <template v-if="shopId === 'all'">
          <div v-for="group in groups" :key="group.shop_id" class="shop-group">
            <div class="shop-group-title">
              <span class="group-bar"></span>
              <span>{{ group.shop_name }}</span>
              <span class="group-count">{{ group.items.filter((i) => i.status === 'todo').length }}</span>
            </div>
            <div v-for="item in group.items" :key="item.id" class="task-row">
              <el-checkbox :model-value="item.status === 'done'" @change="toggle(item)" />
              <span class="task-title" :class="{ done: item.status === 'done' }">{{ item.title }}</span>
              <el-tag v-if="item.carried > 0" size="small" type="warning" effect="plain">
                未完成顺延 {{ item.carried }} 天
              </el-tag>
              <el-button link size="small" class="del-btn" @click="remove(item)">删除</el-button>
            </div>
          </div>
        </template>

        <!-- 单店：平铺 -->
        <template v-else>
          <div v-for="item in items" :key="item.id" class="task-row">
            <el-checkbox :model-value="item.status === 'done'" @change="toggle(item)" />
            <span class="task-title" :class="{ done: item.status === 'done' }">{{ item.title }}</span>
            <el-tag v-if="item.carried > 0" size="small" type="warning" effect="plain">
              未完成顺延 {{ item.carried }} 天
            </el-tag>
            <el-button link size="small" class="del-btn" @click="remove(item)">删除</el-button>
          </div>
        </template>

        <el-empty
          v-if="!loading && items.length === 0 && overdue.length === 0"
          description="这个周期今天没有工作"
          :image-size="60"
        />
      </div>

      <div class="list-footer">
        <span>今日已完成 {{ progress.done }} / {{ progress.total }}</span>
        <span class="hint">清单由模板自动生成，临时的事去「待办」</span>
      </div>
    </div>

    <!-- 店铺管理 -->
    <el-dialog v-model="shopDialog" title="管理店铺" width="480px">
      <div class="shop-form">
        <el-input v-model="newShopName" placeholder="店铺名，如 ICBU 主店" maxlength="40" />
        <el-button type="primary" :loading="savingShop" @click="createShop">添加</el-button>
      </div>
      <el-table :data="shops" size="small" max-height="280">
        <el-table-column prop="name" label="店铺名" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.active ? 'success' : 'info'" size="small">
              {{ row.active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="toggleShop(row)">
              {{ row.active ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="shopDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { api } from '../api.js'

const shops = ref([])
const items = ref([])
const groups = ref([])
const counts = ref({ daily: 0, weekly: 0, monthly: 0 })
const overdue = ref([])
const progress = ref({ done: 0, total: 0 })

const loading = ref(false)
const shopId = ref('all')
const period = ref('daily')

const shopDialog = ref(false)
const newShopName = ref('')
const savingShop = ref(false)

const periodTabs = [
  { value: 'daily', label: '每日' },
  { value: 'weekly', label: '每周' },
  { value: 'monthly', label: '每月' }
]

const shopTabs = computed(() => [
  { value: 'all', label: '全部' },
  ...shops.value.map((s) => ({ value: String(s.id), label: s.short_name || s.name }))
])

const todayText = computed(() => {
  const now = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  const week = ['日', '一', '二', '三', '四', '五', '六'][now.getDay()]
  const p = (n) => String(n).padStart(2, '0')
  return `今天 ${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())} 周${week}`
})

async function loadShops() {
  shops.value = await api.shops.list()
}

async function loadTasks() {
  loading.value = true
  try {
    const data = await api.tasks.list({ shopId: shopId.value, period: period.value })
    items.value = data.items
    groups.value = data.groups
    counts.value = data.counts
    overdue.value = data.overdue
    progress.value = data.progress
  } catch (err) {
    ElMessage.error(err.message || '加载清单失败')
  } finally {
    loading.value = false
  }
}

function switchShop(value) {
  shopId.value = value
  loadTasks()
}

function switchPeriod(value) {
  period.value = value
  loadTasks()
}

async function toggle(item) {
  try {
    await api.tasks.toggle(item.id)
    await loadTasks()
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
    await api.tasks.remove(item.id)
    await loadTasks()
  } catch (err) {
    ElMessage.error(err.message || '删除失败')
  }
}

async function abandon(item) {
  try {
    await api.tasks.abandon(item.id)
    ElMessage.success('已放弃该项')
    await loadTasks()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  }
}

function openShopDialog() {
  newShopName.value = ''
  shopDialog.value = true
}

async function createShop() {
  const name = newShopName.value.trim()
  if (!name) {
    ElMessage.warning('请输入店铺名')
    return
  }
  savingShop.value = true
  try {
    await api.shops.create({ name })
    newShopName.value = ''
    await loadShops()
    ElMessage.success('已添加')
  } catch (err) {
    ElMessage.error(err.message || '添加失败')
  } finally {
    savingShop.value = false
  }
}

async function toggleShop(row) {
  try {
    await api.shops.update(row.id, { active: row.active ? 0 : 1 })
    await loadShops()
    await loadTasks()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  }
}

onMounted(async () => {
  try {
    await loadShops()
    // 进入页面即生成当天条目（接口幂等，重复调用无副作用）
    await api.tasks.generate()
    await loadTasks()
  } catch (err) {
    ElMessage.error(err.message || '初始化失败')
  }
})
</script>

<style scoped>
.header-left {
  display: flex;
  align-items: baseline;
}

.shop-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.list-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0 12px 8px;
}

.period-tabs {
  display: flex;
  gap: 20px;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}

.period-tab {
  height: 42px;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.period-tab.active {
  color: #409eff;
  border-bottom-color: #409eff;
}

.badge {
  font-size: 12px;
  background: #f4f4f5;
  color: #909399;
  border-radius: 8px;
  padding: 0 5px;
}

.badge-active {
  background: #ecf5ff;
  color: #409eff;
}

.list-body {
  flex: 1;
  min-height: 0;
  padding-top: 6px;
}

.overdue-box {
  background: #fdf6ec;
  border: 1px solid #faecd8;
  border-left: 2px solid #e6a23c;
  border-radius: 3px;
  padding: 6px 10px;
  margin-bottom: 8px;
}

.overdue-title {
  font-size: 13px;
  color: #b88230;
  margin-bottom: 2px;
}

.overdue-row {
  height: 28px;
}

.overdue-text {
  color: #8a6d3b;
}

.overdue-days {
  font-size: 13px;
  color: #b88230;
}

.shop-group + .shop-group {
  margin-top: 6px;
}

.shop-group-title {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  font-size: 13px;
  color: #909399;
}

.group-bar {
  width: 2px;
  height: 11px;
  background: #409eff;
  border-radius: 1px;
}

.group-count {
  color: #c0c4cc;
}

.task-row {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 38px;
}

.task-title {
  flex: 1;
  font-size: 14px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-title.done {
  color: #c0c4cc;
  text-decoration: line-through;
}

.del-btn {
  color: #c0c4cc !important;
}

.list-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid #f5f7fa;
  font-size: 13px;
  color: #909399;
  flex-shrink: 0;
}

.hint {
  color: #c0c4cc;
}

.empty-guide {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.guide-steps {
  display: flex;
  gap: 18px;
  margin-bottom: 16px;
  color: #606266;
  font-size: 14px;
}

.guide-step b {
  display: inline-block;
  width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 50%;
  background: #ecf5ff;
  color: #409eff;
  font-size: 13px;
  margin-right: 4px;
}

.guide-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.shop-form {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
</style>
