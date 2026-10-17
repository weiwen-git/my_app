<template>
  <div class="login-wrap">
    <div class="login-card">
      <div class="login-brand">
        <div class="brand-mark"></div>
        <span>个人工作台</span>
      </div>

      <el-form :model="form" label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            autocomplete="current-password"
            @keyup.enter="submit"
          />
        </el-form-item>

        <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon class="login-error" />

        <el-button type="primary" class="login-btn" :loading="loading" @click="submit">登 录</el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api.js'
import { setUser } from '../auth.js'

const router = useRouter()
const route = useRoute()

const form = reactive({ username: 'weiwen', password: '' })
const loading = ref(false)
const error = ref('')

async function submit() {
  if (loading.value) return
  error.value = ''

  if (!form.username.trim() || !form.password) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  try {
    const me = await api.auth.login(form.username.trim(), form.password)
    setUser(me)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/worklist'
    router.replace(redirect)
  } catch (err) {
    error.value = err.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}

.login-card {
  width: 340px;
  padding: 28px 28px 24px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 22px;
  font-size: 16px;
  font-weight: 500;
}

.brand-mark {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  background: #409eff;
}

.login-error {
  margin-bottom: 14px;
}

.login-btn {
  width: 100%;
}
</style>
