<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">翻译</h2>
        <el-tag size="small" type="warning" effect="plain">功能开发中</el-tag>
      </div>
    </div>

    <div class="card-block trans-card">
      <div class="trans-head">
        <span>{{ fromLabel }}</span>
        <el-button link @click="swap" title="交换语言">⇄</el-button>
        <span>{{ toLabel }}</span>
      </div>

      <div class="trans-body">
        <textarea v-model="source" class="trans-input" placeholder="输入要翻译的内容"></textarea>
        <div class="trans-output">
          <span v-if="!translated" class="placeholder">译文会显示在这里</span>
          <span v-else>{{ translated }}</span>
        </div>
      </div>

      <div class="trans-foot">
        <span class="tip">翻译接口尚未接入，本期只提供界面。点击下方按钮不会有任何请求发出。</span>
        <el-button type="primary" :disabled="true">翻译</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const source = ref('')
const translated = ref('')
const isZh = ref(true)

const fromLabel = computed(() => (isZh.value ? '中文' : 'English'))
const toLabel = computed(() => (isZh.value ? 'English' : '中文'))

function swap() {
  isZh.value = !isZh.value
  source.value = ''
  translated.value = ''
}
</script>

<style scoped>
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.trans-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 12px 14px;
}

.trans-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
  font-size: 14px;
  color: #606266;
  flex-shrink: 0;
}

.trans-body {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 12px;
  padding: 10px 0;
}

.trans-input {
  flex: 1;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  font-family: inherit;
  resize: none;
  outline: none;
}

.trans-output {
  flex: 1;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
  background: #fafafa;
  overflow-y: auto;
}

.placeholder {
  color: #c0c4cc;
}

.trans-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
  flex-shrink: 0;
  gap: 12px;
}

.tip {
  font-size: 13px;
  color: #909399;
}
</style>
