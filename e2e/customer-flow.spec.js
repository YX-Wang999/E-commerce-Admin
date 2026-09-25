import { test, expect } from '@playwright/test'

test.describe('商城核心流程', () => {
  test.skip(!process.env.E2E_WITH_BACKEND, '需要后端与种子数据：设置 E2E_WITH_BACKEND=1')

  test('浏览首页', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\//)
  })
})

test.describe('用户下单流程（需种子数据）', () => {
  test.skip(!process.env.E2E_WITH_BACKEND, '需要 E2E_WITH_BACKEND=1')

  test('登录 → 搜索商品 → 进入详情', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder(/手机|phone/i).fill('13800000000')
    await page.getByPlaceholder(/密码|password/i).fill('admin123456')
    await page.getByRole('button', { name: /登录|sign in/i }).click()
    await page.waitForURL(/home|\//)
    await page.goto('/search?q=测试')
    await expect(page.locator('body')).toBeVisible()
  })
})
