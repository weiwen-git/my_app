<template>
  <el-dialog :model-value="visible" title="管理列" width="640px" @update:model-value="$emit('update:visible', $event)">
    <div class="col-add">
      <el-input v-model="newName" size="small" placeholder="新列名" maxlength="30" style="width: 160px" />
      <el-select v-model="newType" size="small" style="width: 100px">
        <el-option label="数字" value="number" />
        <el-option label="文本" value="text" />
        <el-option label="日期" value="date" />
      </el-select>
      <el-select v-if="newType === 'number'" v-model="newAgg" size="small" style="width: 100px">
        <el-option label="求和" value="sum" />
        <el-option label="平均" value="avg" />
        <el-option label="不合计" value="none" />
      </el-select>
      <el-button type="primary" size="small" :loading="adding" @click="addColumn">添加列</el-button>
    </div>

    <el-table :data="draft" size="small" max-height="360">
      <el-table-column label="列名" min-width="150">
        <template #default="{ row }">
          <el-input v-model="row.name" size="small" maxlength="30" @change="save(row)" />
        </template>
      </el-table-column>

      <el-table-column label="类型" width="110">
        <template #default="{ row }">
          <el-select v-model="row.type" size="small" @change="save(row)">
            <el-option label="数字" value="number" />
            <el-option label="文本" value="text" />
            <el-option label="日期" value="date" />
          </el-select>
        </template>
      </el-table-column>

      <el-table-column label="合计" width="110">
        <template #default="{ row }">
          <el-select
            v-model="row.agg"
            size="small"
            :disabled="row.type !== 'number'"
            @change="save(row)"
          >
            <el-option label="求和" value="sum" />
            <el-option label="平均" value="avg" />
            <el-option label="不合计" value="none" />
          </el-select>
        </template>
      </el-table-column>

      <el-table-column label="顺序" width="90">
        <template #default="{ $index }">
          <el-button link size="small" :disabled="$index === 0" @click="move($index, -1)">↑</el-button>
          <el-button link size="small" :disabled="$index === draft.length - 1" @click="move($index, 1)">
            ↓
          </el-button>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="70" align="right">
        <template #default="{ row }">
          <el-button link type="danger" size="small" @click="removeColumn(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="tip">改列名/类型/合计方式后会自动保存；删除列会连同该列数据一起删除。</div>

    <template #footer>
      <el-button type="primary" @click="$emit('update:visible', false)">完成</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../../api.js'

const props = defineProps({
  visible: Boolean,
  sheetId: { type: [Number, String], required: true },
  columns: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:visible', 'changed'])

const draft = ref([])
const newName = ref('')
const newType = ref('number')
const newAgg = ref('sum')
const adding = ref(false)

watch(
  () => props.visible,
  (v) => {
    if (v) draft.value = props.columns.map((c) => ({ ...c }))
  },
  { immediate: true }
)

async function refresh() {
  emit('changed')
}

async function addColumn() {
  const name = newName.value.trim()
  if (!name) {
    ElMessage.warning('请输入列名')
    return
  }
  adding.value = true
  try {
    await api.sheets.addColumn(props.sheetId, {
      name,
      type: newType.value,
      agg: newType.value === 'number' ? newAgg.value : 'none'
    })
    newName.value = ''
    ElMessage.success('已添加')
    await refresh()
  } catch (err) {
    ElMessage.error(err.message || '添加失败')
  } finally {
    adding.value = false
  }
}

async function save(row) {
  try {
    await api.sheets.updateColumn(props.sheetId, row.id, {
      name: row.name,
      type: row.type,
      agg: row.type === 'number' ? row.agg : 'none'
    })
    await refresh()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
    await refresh() // 回滚显示
  }
}

async function removeColumn(row) {
  try {
    await ElMessageBox.confirm(
      `删除列「${row.name}」？该列已有的数据会一并删除，无法恢复。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await api.sheets.removeColumn(props.sheetId, row.id)
    ElMessage.success('已删除')
    await refresh()
  } catch (err) {
    ElMessage.error(err.message || '删除失败')
  }
}

async function move(index, delta) {
  const target = draft.value[index + delta]
  const current = draft.value[index]
  if (!target || !current) return
  try {
    await api.sheets.updateColumn(props.sheetId, current.id, { sort_order: target.sort_order })
    await api.sheets.updateColumn(props.sheetId, target.id, { sort_order: current.sort_order })
    await refresh()
  } catch (err) {
    ElMessage.error(err.message || '调整失败')
  }
}
</script>

<style scoped>
.col-add {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.tip {
  margin-top: 10px;
  font-size: 13px;
  color: #909399;
}
</style>
