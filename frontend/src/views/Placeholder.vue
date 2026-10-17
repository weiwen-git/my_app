<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">{{ title }}</h2>
        <span class="page-sub">模块开发中</span>
      </div>
    </div>

    <div class="card-block holder">
      <el-empty :description="`「${title}」将在后续批次实现`" :image-size="80">
        <template #description>
          <p style="margin: 0 0 6px">「{{ title }}」还没做</p>
          <p style="margin: 0; font-size: 13px; color: #909399">
            第一批已完成：工作清单。其余模块按 PRD 分批上线。
          </p>
        </template>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => route.meta.title || '页面')
</script>

<style scoped>
.header-left {
  display: flex;
  align-items: baseline;
}

.holder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
