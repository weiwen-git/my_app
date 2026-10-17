/**
 * 第二批模块的端到端走查：模板管理、待办、便签、笔记、数据表、翻译。
 * 运行：node .e2e/modules.cjs
 */
const { chromium } = require('playwright-core')
const path = require('path')
const fs = require('fs')

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const BASE = 'http://127.0.0.1:5173'
const SHOTS = path.join(__dirname, 'shots2')

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
  const requests = []
  page.on('console', (m) => {
    if (m.type() === 'error') consoleErrors.push(m.text())
  })
  page.on('pageerror', (e) => consoleErrors.push('pageerror: ' + e.message))
  page.on('request', (r) => requests.push(r.url()))

  const shot = async (name) => {
    shotIndex += 1
    await page.screenshot({ path: path.join(SHOTS, `${String(shotIndex).padStart(2, '0')}-${name}.png`) })
  }

  const menu = (text) => page.locator('.side-menu').getByText(text, { exact: true }).first()

  try {
    // ---------- 登录 ----------
    await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(700)
    await page.locator('.login-card input').first().fill('weiwen')
    await page.locator('.login-card input[type="password"]').first().fill('admin123')
    await page.locator('.login-card button').last().click()
    await page.waitForURL('**/worklist', { timeout: 10000 })
    await page.waitForTimeout(700)

    // ---------- 模板管理 ----------
    await page.locator('button', { hasText: '管理模板' }).click()
    await page.waitForURL('**/worklist/templates', { timeout: 8000 })
    await page.waitForTimeout(900)
    const tplRows = await page.locator('.el-table__row').count()
    record('模板管理页列出模板', tplRows > 0, `${tplRows} 条`)
    await shot('templates')

    // 新建模板
    const tplTitle = `E2E 每日检查 ${Date.now() % 1000}`
    await page.locator('button', { hasText: '新建模板' }).click()
    await page.waitForTimeout(500)
    await page.locator('.el-dialog input').first().fill(tplTitle)
    // 选店铺（下拉会 teleport 到 body，页面上有多个实例，只点可见的那个）
    await page.locator('.el-dialog .el-select').first().click()
    await page.waitForTimeout(500)
    await page.locator('.el-select-dropdown__item:visible').first().click()
    await page.waitForTimeout(300)
    await page.locator('.el-dialog button', { hasText: '保存' }).click()
    await page.waitForTimeout(1200)
    const tplFound = await page.locator('.el-table__row', { hasText: tplTitle }).count()
    record('新建模板成功', tplFound > 0, tplTitle)
    await shot('template-created')

    // ---------- 待办 ----------
    await menu('待办').click()
    await page.waitForTimeout(800)
    const todoTitle = `E2E 临时任务 ${Date.now() % 1000}`
    await page.locator('button', { hasText: '新增待办' }).click()
    await page.waitForTimeout(500)
    await page.locator('.el-dialog input').first().fill(todoTitle)
    await page.locator('.el-dialog button', { hasText: '保存' }).click()
    await page.waitForTimeout(1000)
    const todoFound = await page.locator('.todo-row', { hasText: todoTitle }).count()
    record('新增待办成功', todoFound > 0, todoTitle)
    await shot('todos')

    // 完成它
    const targetRow = page.locator('.todo-row', { hasText: todoTitle }).first()
    await targetRow.locator('.el-checkbox').click()
    await page.waitForTimeout(1000)
    const doneCount = await page.locator('.done-bar').innerText()
    record('待办完成后进入已完成区', /已完成\s*\d+/.test(doneCount), doneCount.replace(/\s+/g, ' '))

    // ---------- 便签 ----------
    await menu('便签').click()
    await page.waitForTimeout(800)
    await page.locator('button', { hasText: '新建便签' }).click()
    await page.waitForTimeout(700)
    const stickyText = `E2E 便签 ${Date.now() % 1000}`
    const ta = page.locator('.sticky-text').first()
    await ta.fill(stickyText)
    await page.locator('.page-header').click() // 触发 blur
    await page.waitForTimeout(900)
    const stickySaved = await page.locator('.sticky-text').first().inputValue()
    record('便签输入并保存', stickySaved === stickyText, stickySaved)
    await shot('sticky')

    // ---------- 笔记 ----------
    await menu('笔记').click()
    await page.waitForTimeout(800)
    await page.locator('button', { hasText: '新建笔记' }).click()
    await page.waitForTimeout(900)
    const noteTitle = `E2E 笔记 ${Date.now() % 1000}`
    await page.locator('.title-input').fill(noteTitle)
    await page.locator('.content-input').fill('这是端到端测试写入的正文。\n第二行内容。')
    await page.waitForTimeout(2000) // 等自动保存
    const saveState = await page.locator('.save-state').innerText()
    record('笔记自动保存', saveState.includes('已保存'), saveState)
    const noteInList = await page.locator('.note-item', { hasText: noteTitle }).count()
    record('笔记出现在列表', noteInList > 0)
    await shot('notes')

    // ---------- 数据表 ----------
    await menu('数据').click()
    await page.waitForTimeout(500)
    await page.locator('.side-menu').getByText('ICBU 周数据', { exact: true }).first().click()
    await page.waitForTimeout(1000)
    const dataRows = await page.locator('.el-table__row').count()
    record('数据表详情列出记录', dataRows > 0, `${dataRows} 行`)
    const summaryText = await page.locator('.el-table__footer').innerText().catch(() => '')
    record('表格有合计行', /合计/.test(summaryText), summaryText.replace(/\s+/g, ' ').slice(0, 90))
    await shot('sheet-detail')

    // 管理列弹窗
    await page.locator('button', { hasText: '管理列' }).click()
    await page.waitForTimeout(700)
    const colRows = await page.locator('.el-dialog .el-table__row').count()
    record('列管理弹窗列出列', colRows > 0, `${colRows} 列`)
    await shot('column-manager')
    await page.locator('.el-dialog button', { hasText: '完成' }).click()
    await page.waitForTimeout(400)

    // 新增记录
    await page.locator('button', { hasText: '新增记录' }).click()
    await page.waitForTimeout(700)
    const numInputs = await page.locator('.el-dialog .el-input-number input').count()
    record('新增记录弹窗按列生成数字输入框', numInputs > 0, `${numInputs} 个数字框`)
    await shot('row-editor')
    await page.locator('.el-dialog button', { hasText: '取消' }).click()
    await page.waitForTimeout(400)

    // CSV 导入
    await page.locator('button', { hasText: '粘贴 CSV' }).click()
    await page.waitForTimeout(600)
    const csvHint = await page.locator('.csv-tip').innerText()
    record('CSV 弹窗显示列顺序提示', csvHint.includes('周起始日'), csvHint.split('\n')[0].slice(0, 40))
    await page.locator('.el-dialog textarea').fill('2026-09-14,20,5000,180,2.8,E2E导入')
    await page.locator('.el-dialog button', { hasText: '导入' }).click()
    await page.waitForTimeout(1200)
    const rowsAfter = await page.locator('.el-table__row').count()
    record('CSV 导入后行数增加', rowsAfter > dataRows, `${dataRows} → ${rowsAfter}`)
    await shot('csv-import')

    // ---------- 翻译 ----------
    requests.length = 0
    await menu('翻译').click()
    await page.waitForTimeout(800)
    const transBtn = page.locator('button', { hasText: '翻译' }).last()
    const disabled = await transBtn.isDisabled()
    record('翻译按钮为禁用状态（不假装能用）', disabled)
    await shot('translate')
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
  console.log(consoleErrors.length ? consoleErrors.slice(0, 8).join('\n') : '（无）')

  const failed = results.filter((r) => !r.ok)
  console.log(`\n===== 汇总：${results.length - failed.length}/${results.length} 通过 =====`)
  fs.writeFileSync(path.join(__dirname, 'result2.json'), JSON.stringify({ results, consoleErrors }, null, 2))
}

main()
