/**
 * 端到端走查脚本：用系统 Chrome 真实操作一遍完整流程。
 * 运行：node .e2e/walkthrough.cjs
 */
const { chromium } = require('playwright-core')
const path = require('path')
const fs = require('fs')

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const BASE = 'http://127.0.0.1:5173'
const SHOTS = path.join(__dirname, 'shots')

const results = []
let shotIndex = 0

function record(name, ok, detail) {
  results.push({ name, ok, detail })
  console.log(`${ok ? '  OK ' : ' FAIL'}  ${name}${detail ? ' — ' + detail : ''}`)
}

async function main() {
  fs.mkdirSync(SHOTS, { recursive: true })

  const browser = await chromium.launch({ executablePath: CHROME, headless: true })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await context.newPage()

  const consoleErrors = []
  const failedRequests = []
  page.on('console', (m) => {
    if (m.type() === 'error') consoleErrors.push(m.text())
  })
  page.on('pageerror', (e) => consoleErrors.push('pageerror: ' + e.message))
  page.on('requestfailed', (r) => {
    const url = r.url()
    if (!url.includes('favicon')) failedRequests.push(`${r.method()} ${url} — ${r.failure()?.errorText}`)
  })

  const shot = async (name) => {
    shotIndex += 1
    const file = path.join(SHOTS, `${String(shotIndex).padStart(2, '0')}-${name}.png`)
    await page.screenshot({ path: file })
    return file
  }

  try {
    // ---------- 1. 未登录访问首页 ----------
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(800)
    const urlAfterEntry = page.url()
    record('未登录自动跳转登录页', urlAfterEntry.includes('/login'), urlAfterEntry)
    await shot('login')

    // ---------- 2. 登录 ----------
    const userInput = page.locator('.login-card input').first()
    const pwdInput = page.locator('.login-card input[type="password"]').first()
    await userInput.fill('weiwen')
    await pwdInput.fill('admin123')
    await page.locator('.login-card button').last().click()

    await page.waitForURL('**/worklist', { timeout: 10000 })
    await page.waitForTimeout(900)
    record('登录成功并进入工作清单', page.url().includes('/worklist'), page.url())
    await shot('worklist')

    // ---------- 3. 检查清单内容 ----------
    const shopTabCount = await page.locator('.shop-tabs button').count()
    record('店铺 Tab 已渲染', shopTabCount >= 2, `找到 ${shopTabCount} 个按钮（含齿轮）`)

    const rows = page.locator('.task-row')
    const rowCount = await rows.count()
    record('清单有条目', rowCount > 0, `共 ${rowCount} 行`)

    const groupTitles = await page.locator('.shop-group-title').allInnerTexts()
    record('「全部」视图按店铺分组', groupTitles.length > 0, groupTitles.map((t) => t.replace(/\s+/g, ' ')).join(' / '))

    // ---------- 4. 勾选一条「未完成」的 ----------
    const progressBefore = (await page.locator('.list-footer').innerText()).replace(/\s+/g, ' ')
    const doneBefore = Number((progressBefore.match(/已完成\s*(\d+)/) || [])[1] || 0)
    record('底部显示完成进度', /已完成\s*\d+\s*\/\s*\d+/.test(progressBefore), progressBefore)

    const firstUnchecked = page.locator('.task-row .el-checkbox:not(.is-checked)').first()
    if ((await firstUnchecked.count()) === 0) {
      record('勾选后完成数 +1', false, '当前没有未完成项可供勾选')
    } else {
      await firstUnchecked.click()
      await page.waitForTimeout(900)
      const progressAfter = (await page.locator('.list-footer').innerText()).replace(/\s+/g, ' ')
      const doneAfter = Number((progressAfter.match(/已完成\s*(\d+)/) || [])[1] || 0)
      record('勾选后完成数 +1', doneAfter === doneBefore + 1, `${doneBefore} → ${doneAfter}`)
      await shot('task-checked')
    }

    // ---------- 5. 切换店铺 ----------
    await page.locator('.shop-tabs button', { hasText: '1688' }).first().click()
    await page.waitForTimeout(700)
    const groupAfterFilter = await page.locator('.shop-group-title').count()
    const rowsAfterFilter = await page.locator('.task-row').count()
    record('切到单店后不再分组', groupAfterFilter === 0, `分组块 ${groupAfterFilter} 个，条目 ${rowsAfterFilter} 行`)
    await shot('shop-filtered')

    // ---------- 6. 切换周期 ----------
    await page.locator('.period-tab', { hasText: '每周' }).click()
    await page.waitForTimeout(700)
    const weeklyEmpty = await page.locator('.el-empty').count()
    record('周期切换到「每周」', true, weeklyEmpty > 0 ? '显示空态（今天周六无每周任务）' : '有数据')
    await shot('period-weekly')

    // ---------- 7. 店铺管理弹窗 ----------
    await page.locator('.shop-tabs button[title="管理店铺"]').click()
    await page.waitForTimeout(600)
    const dialogVisible = await page.locator('.el-dialog').isVisible()
    record('店铺管理弹窗可打开', dialogVisible)
    await shot('shop-dialog')

    // ---------- 8. 新增店铺 ----------
    const testShop = `测试店${Date.now() % 10000}`
    await page.locator('.el-dialog input').first().fill(testShop)
    await page.locator('.el-dialog button', { hasText: '添加' }).click()
    await page.waitForTimeout(900)
    const shopNames = await page.locator('.el-dialog .el-table__row td:first-child').allInnerTexts()
    record('新增店铺成功', shopNames.some((n) => n.includes(testShop)), shopNames.join(' / '))
    await shot('shop-added')
    await page.locator('.el-dialog button', { hasText: '关闭' }).click()
    await page.waitForTimeout(400)

    // ---------- 9. 侧边栏进入数据总览 ----------
    const subMenuTitle = page.locator('.side-menu .el-sub-menu__title').first()
    if (!(await page.locator('.side-menu').getByText('全部数据表').isVisible().catch(() => false))) {
      await subMenuTitle.click()
      await page.waitForTimeout(500)
    }
    const dataEntry = page.locator('.side-menu').getByText('全部数据表', { exact: true }).first()
    const hasDataEntry = await dataEntry.isVisible().catch(() => false)
    record('「数据」子菜单已展开且有总览入口', hasDataEntry)
    if (hasDataEntry) {
      await dataEntry.click()
      await page.waitForTimeout(700)
    }
    record('点「全部数据表」进入总览页', page.url().endsWith('/data'), `当前 URL：${page.url()}`)
    await shot('data-overview')

    // ---------- 10. 新建数据表 ----------
    const sheetRows = await page.locator('.el-table__row').count()
    record('总览页列出了数据表', sheetRows > 0, `${sheetRows} 张`)

    const testSheet = `测试表${Date.now() % 10000}`
    await page.locator('button', { hasText: '新建数据表' }).first().click()
    await page.waitForTimeout(500)
    await page.locator('.el-dialog input').first().fill(testSheet)
    await page.locator('.el-dialog button', { hasText: '创建' }).click()
    await page.waitForTimeout(1200)
    record('新建数据表并自动跳转', /\/data\/\d+$/.test(page.url()), page.url())
    await shot('sheet-created')

    // ---------- 11. 占位模块 ----------
    await page.locator('.side-menu').getByText('待办', { exact: true }).first().click()
    await page.waitForTimeout(600)
    record('待办页可进入（当前为占位）', page.url().includes('/todos'), page.url())
    await shot('todos-placeholder')

    // ---------- 12. 退出登录 ----------
    await page.locator('.header-right button').click()
    await page.waitForTimeout(900)
    record('退出后回到登录页', page.url().includes('/login'), page.url())
    await shot('logout')

    // 退出后刷新受保护页面应被拦回登录
    await page.goto(BASE + '/worklist', { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(800)
    record('退出后访问受限页被拦回登录', page.url().includes('/login'), page.url())
  } catch (err) {
    record('流程中断', false, err.message)
    try {
      await shot('crash')
    } catch {
      /* ignore */
    }
  } finally {
    await browser.close()
  }

  console.log('\n===== 控制台错误 =====')
  console.log(consoleErrors.length ? consoleErrors.slice(0, 10).join('\n') : '（无）')
  console.log('\n===== 失败请求 =====')
  console.log(failedRequests.length ? failedRequests.slice(0, 10).join('\n') : '（无）')

  const failed = results.filter((r) => !r.ok)
  console.log(`\n===== 汇总：${results.length - failed.length}/${results.length} 通过 =====`)
  fs.writeFileSync(path.join(__dirname, 'result.json'), JSON.stringify({ results, consoleErrors, failedRequests }, null, 2))
  process.exitCode = failed.length ? 1 : 0
}

main()
