import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router.js'
import './style.css'

const app = createApp(App)

// 图标全局注册，模板里可直接 <el-icon><Plus /></el-icon>
for (const [name, comp] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, comp)
}

app.use(ElementPlus, { locale: zhCn })
app.use(router)
app.mount('#app')
