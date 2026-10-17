/** 只读截图：不改数据，用于确认视觉。 */
const { chromium } = require('playwright-core')
const path = require('path')
const fs = require('fs')

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const BASE = 'http://127.0.0.1:5173'
const OUT = path.join(__dirname, 'shots3')

;(async () => {
  fs.mkdirSync(OUT, { recursive: true })
  const browser = await chromium.launch({ executablePath: CHROME, headless: true })
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })

  await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(600)
  await page.locator('.login-card input').first().fill('weiwen')
  await page.locator('.login-card input[type="password"]').first().fill('admin123')
  await page.locator('.login-card button').last().click()
  await page.waitForURL('**/worklist', { timeout: 10000 })
  await page.waitForTimeout(1200)

  await page.screenshot({ path: path.join(OUT, 'worklist.png') })

  // 数据表
  await page.locator('.side-menu').getByText('ICBU 周数据', { exact: true }).first().click()
  await page.waitForTimeout(1200)
  await page.screenshot({ path: path.join(OUT, 'sheet.png') })

  // 待办
  await page.locator('.side-menu').getByText('待办', { exact: true }).first().click()
  await page.waitForTimeout(900)
  await page.screenshot({ path: path.join(OUT, 'todos.png') })

  await browser.close()
  console.log('shots done')
})()
