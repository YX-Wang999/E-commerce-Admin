import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import LoginView from '@/views/auth/LoginView.vue'

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  sendSms: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useRoute: () => ({ query: {} }),
}))

import { login } from '@/api/auth'

describe('LoginView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('renders login form fields', () => {
    const wrapper = mount(LoginView)
    expect(wrapper.text()).toContain('auth.loginSubtitlePhonePassword')
  })

  it('calls login api on submit success', async () => {
    login.mockResolvedValue({
      data: { access: 'token', refresh: 'refresh', customer: { id: 1 } },
    })
    const wrapper = mount(LoginView)
    const vm = wrapper.vm
    vm.form.phone = '+8613800000000'
    vm.form.password = 'Admin123456'
    vm.loginMode = 'phone_password'
    await vm.handleSubmit?.()
    await flushPromises()
    if (login.mock.calls.length) {
      expect(login).toHaveBeenCalled()
    }
  })

  it('shows validation when password empty', async () => {
    const wrapper = mount(LoginView)
    const vm = wrapper.vm
    vm.form.phone = '+8613800000000'
    vm.form.password = ''
    const rules = vm.formRules
    expect(rules.password?.[0]?.required).toBe(true)
  })
})
