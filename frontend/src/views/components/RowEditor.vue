<template>
  <el-dialog
    :model-value="visible"
    :title="row ? '编辑记录' : '新增记录'"
    width="460px"
    @update:model-value="$emit('update:visible', $event)"
  >
    <el-form label-width="100px">
      <el-form-item v-for="col in sortedColumns" :key="col.id" :label="col.name">
        <el-input-number
          v-if="col.type === 'number'"
          v-model="values[String(col.id)]"
          :controls="false"
          style="width: 100%"
          placeholder="填数字"
        />
        <el-date-picker
          v-else-if="col.type === 'date'"
          v-model="values[String(col.id)]"
          type="date"
          value-format="YYYY-MM-DD"
          style="width: 100%"
          placeholder="选日期"
        />
        <el-input v-else v-model="values[String(col.id)]" maxlength="200" placeholder="填文本" />
      </el-form-item>

      <el-empty v-if="sortedColumns.length === 0" description="这张表还没有列" :image-size="50" />
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../../api.js'

const props = defineProps({
  visible: Boolean,
  sheetId: { type: [Number, String], required: true },
  columns: { type: Array, default: () => [] },
  row: { type: Object, default: null }
})
const emit = defineEmits(['update:visible', 'changed'])

const values = reactive({})
const saving = ref(false)

const sortedColumns = computed(() =>
  [...props.columns].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
)

watch(
  () => props.visible,
  (v) => {
    if (!v) return
    Object.keys(values).forEach((k) => delete values[k])
    if (props.row?.values) {
      Object.assign(values, { ...props.row.values })
    }
  }
)

async function save() {
  if (saving.value) return
  saving.value = true
  try {
    const payload = {}
    for (const col of sortedColumns.value) {
      const key = String(col.id)
      const raw = values[key]
      payload[key] = raw === undefined || raw === null ? '' : raw
    }
    if (props.row) {
      await api.sheets.updateRow(props.sheetId, props.row.id, payload)
    } else {
      await api.sheets.addRow(props.sheetId, payload)
    }
    ElMessage.success('已保存')
    emit('update:visible', false)
    emit('changed')
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>
