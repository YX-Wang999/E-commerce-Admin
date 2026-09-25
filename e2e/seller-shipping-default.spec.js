import { test, expect } from '@playwright/test'

const sellerUsername = process.env.E2E_SELLER_USERNAME
const sellerPassword = process.env.E2E_SELLER_PASSWORD

test.describe('商家默认快递', () => {
  test.skip(
    !sellerUsername || !sellerPassword,
    '需要 E2E_SELLER_USERNAME 和 E2E_SELLER_PASSWORD；通过商家登录页正常认证，不绕过登录。',
  )

  test('订单列表发货弹窗默认选中店铺配置的快递，且允许手动切换', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('商户名称或手机号').fill(sellerUsername)
    await page.getByPlaceholder('密码', { exact: true }).fill(sellerPassword)

    const loginResponsePromise = page.waitForResponse((response) =>
      response.request().method() === 'POST'
      && new URL(response.url()).pathname.endsWith('/api/seller/auth/login/'),
    )
    await page.getByRole('button', { name: '登 录' }).click()
    const loginResponse = await loginResponsePromise
    expect(loginResponse.ok(), '商家账号应通过正常登录接口认证').toBeTruthy()

    const loginPayload = await loginResponse.json()
    const defaultExpressCode = loginPayload.data?.tenant?.config?.default_express_code
    test.skip(!defaultExpressCode, '该测试商家的 tenant.config.default_express_code 未配置。')

    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/dashboard$/)
    await page.getByRole('button', { name: '订单管理', exact: true }).click()
    const expressResponsePromise = page.waitForResponse((response) =>
      response.request().method() === 'GET'
      && new URL(response.url()).pathname.endsWith('/api/seller/express-companies/'),
    )
    await page.getByRole('button', { name: '订单列表', exact: true }).click()
    await expect(page).toHaveURL(/\/orders$/)

    // Use the existing status filter to show paid orders that can be shipped.
    const statusFilter = page.locator('.el-form-item').filter({ hasText: '状态' }).locator('.el-select')
    await statusFilter.click()
    await page.getByRole('option', { name: '已支付', exact: true }).click()
    const ordersResponsePromise = page.waitForResponse((response) =>
      response.request().method() === 'GET'
      && new URL(response.url()).pathname.endsWith('/api/seller/orders/'),
    )
    await page.getByRole('button', { name: '查询', exact: true }).click()

    const expressResponse = await expressResponsePromise
    expect(expressResponse.ok(), '应能读取可用快递列表').toBeTruthy()
    const expressPayload = await expressResponse.json()
    const expressCompanies = expressPayload.data || []
    const defaultCompany = expressCompanies.find((company) => company.code === defaultExpressCode)
    expect(defaultCompany, '店铺默认快递必须存在于可选快递列表').toBeTruthy()

    const ordersResponse = await ordersResponsePromise
    expect(ordersResponse.ok(), '应能读取该商家的订单').toBeTruthy()
    const ordersPayload = await ordersResponse.json()
    test.skip(
      !(ordersPayload.data?.results || []).some((order) => order.status === 'paid'),
      '该测试商家没有已支付订单；请准备一笔不会用于真实履约的测试订单。',
    )

    const shipButton = page.getByRole('button', { name: '发货', exact: true }).first()
    await expect(
      shipButton,
      '需要至少一笔已付款、属于该测试商家的现有订单；本测试不会创建订单',
    ).toBeVisible()
    await shipButton.click()

    const dialog = page.getByRole('dialog', { name: '订单发货' })
    await expect(dialog).toBeVisible()
    const expressSelect = dialog.locator('.el-select input[role="combobox"]')
    await expect(expressSelect).toHaveValue(defaultCompany.name)

    const alternateCompany = expressCompanies.find((company) => company.code !== defaultExpressCode)
    expect(alternateCompany, '至少需要两种可选快递以验证手动切换').toBeTruthy()

    await expressSelect.click()
    await page.locator('.el-select-dropdown:visible .el-select-dropdown__item')
      .filter({ hasText: alternateCompany.name })
      .click()
    await expect(expressSelect).toHaveValue(alternateCompany.name)

    // Close using Cancel: never enter a tracking number or submit the ship action.
    await dialog.getByRole('button', { name: '取消', exact: true }).click()
    await expect(dialog).toBeHidden()
  })
})
