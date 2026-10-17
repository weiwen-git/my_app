<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">模板管理</h2>
        <span class="page-sub">定义哪些工作会按周期自动出现</span>
      </div>
      <el-button type="primary" size="small" @click="openCreate">+ 新建模板</el-button>
    </div>

    <div class="filter-bar">
      <el-select v-model="filterShop" size="small" style="width: 150px" @change="load">
        <el-option label="全部店铺" value="all" />
        <el-option v-for="s in shops" :key="s.id" :label="s.name" :value="String(s.id)" />
      </el-select>
      <el-select v-model="filterPeriod" size="small" style="width: 120px" placeholder="全部周期">
        <el-option label="全部周期" value="all" />
        <el-option label="每日" value="daily" />
        <el-option label="每周" value="weekly" />
        <el-option label="每月" value="monthly" />
      </el-select>
      <span class="count-hint">共 {{ filtered.length }} 条</span>
    </div>

    <div class="card-block table-wrap">
      <el-table v-loading="loading" :data="filtered" size="small" height="100%">
        <el-table-column prop="title" label="工作内容" min-width="200" />
        <el-table-column prop="shop_name" label="店铺" width="120" />
        <el-table-column label="周期" width="130">
          <template #default="{ row }">
            <el-tag size="small" :type="periodTagType(row.repeat_rule)" effect="plain">
              {{ ruleText(row.repeat_rule) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="排序" width="100">
          <template #default="{ row }">
            <el-button link size="small" :disabled="row.sort_order <= 0" @click="move(row, -1)">↑</el-button>
            <el-button link size="small" @click="move(row, 1)">↓</el-button>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.active ? 'success' : 'info'">
              {{ row.active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" align="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button link size="small" @click="toggleActive(row)">{{ row.active ? '停用' : '启用' }}</el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="还没有模板，先建一个" :image-size="70" />
        </template>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑模板' : '新建模板'" width="440px">
      <el-form :model="form" label-width="90px" label-position="right">
        <el-form-item label="工作内容" required>
          <el-input v-model="form.title" placeholder="如：查看昨日询盘" maxlength="80" />
        </el-form-item>
        <el-form-item label="店铺" required>
          <el-select v-model="form.shopId" style="width: 100%" placeholder="选择店铺">
            <el-option v-for="s in shops" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="周期" required>
          <el-radio-group v-model="form.periodType">
            <el-radio-button label="daily">每日</el-radio-button>
            <el-radio-button label="weekly">每周</el-radio-button>
            <el-radio-button label="monthly">每月</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.periodType === 'weekly'" label="周几" required>
          <el-select v-model="form.weekday" style="width: 100%">
            <el-option v-for="(label, idx) in weekLabels" :key="idx" :label="label" :value="idx + 1" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.periodType === 'monthly'" label="几号" required>
          <el-input-number v-model="form.monthday" :min="1" :max="31" />
          <span class="form-hint">当月没有这一天时，落在当月最后一天</span>
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
import { ElMessage } from 'element-plus'
import { api } from '../api.js'

const shops = ref([])
const templates = ref([])
const loading = ref(false)
const filterShop = ref('all')
const filterPeriod = ref('all')

const dialogVisible = ref(false)
const editing = ref(null)
const saving = ref(false)

const weekLabels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const form = reactive({
  title: '',
  shopId: null,
  periodType: 'daily',
  weekday: 1,
  monthday: 1
})

const filtered = computed(() => {
  if (filterPeriod.value === 'all') return templates.value
  return templates.value.filter((t) => t.repeat_rule.startsWith(filterPeriod.value))
})

function ruleText(rule) {
  if (!rule) return '—'
  if (rule === 'daily') return '每日'
  if (rule.startsWith('weekly:')) {
    const n = Number(rule.split(':')[1])
    return `每${weekLabels[n - 1] || ''}`
  }
  if (rule.startsWith('monthly:')) return `每月 ${rule.split(':')[1]} 号`
  return rule
}

function periodTagType(rule) {
  if (rule === 'daily') return 'primary'
  if (rule.startsWith('weekly:')) return 'success'
  return 'warning'
}

async function load() {
  loading.value = true
  try {
    templates.value = await api.templates.list(filterShop.value)
  } catch (err) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.title = ''
  form.shopId = shops.value[0]?.id ?? null
  form.periodType = 'daily'
  form.weekday = 1
  form.monthday = 1
}

function openCreate() {
  editing.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  form.title = row.title
  form.shopId = row.shop_id
  const rule = row.repeat_rule || 'daily'
  if (rule.startsWith('weekly:')) {
    form.periodType = 'weekly'
    form.weekday = Number(rule.split(':')[1])
  } else if (rule.startsWith('monthly:')) {
    form.periodType = 'monthly'
    form.monthday = Number(rule.split(':')[1])
  } else {
    form.periodType = 'daily'
  }
  dialogVisible.value = true
}

function buildRule() {
  if (form.periodType === 'weekly') return `weekly:${form.weekday}`
  if (form.periodType === 'monthly') return `monthly:${form.monthday}`
  return 'daily'
}

async function save() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写工作内容')
    return
  }
  if (!form.shopId) {
    ElMessage.warning('请选择店铺')
    return
  }

  saving.value = true
  try {
    const payload = {
      shop_id: form.shopId,
      title: form.title.trim(),
      repeat_rule: buildRule()
    }
    if (editing.value) {
      await api.templates.update(editing.value.id, payload)
      ElMessage.success('已保存')
    } else {
      const res = await api.templates.create(payload)
      ElMessage.success(res.created_today ? '已创建，并已加入今日清单' : '已创建')
    }
    dialogVisible.value = false
    await load()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleActive(row) {
  try {
    await api.templates.update(row.id, { active: row.active ? 0 : 1 })
    await load()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  }
}

async function move(row, delta) {
  try {
    await api.templates.update(row.id, { sort_order: row.sort_order + delta })
    await load()
  } catch (err) {
    ElMessage.error(err.message || '调整失败')
  }
}

onMounted(async () => {
  try {
    shops.value = await api.shops.list()
  } catch (err) {
    ElMessage.error(err.message || '加载店铺失败')
  }
  await load()
})
</script>

<style scoped>
.header-left {
  display: flex;
  align-items: baseline;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.count-hint {
  font-size: 13px;
  color: #909399;
}

.table-wrap {
  flex: 1;
  min-height: 0;
  padding: 4px;
}

.form-hint {
  margin-left: 10px;
  font-size: 13px;
  color: #909399;
}
</style>
