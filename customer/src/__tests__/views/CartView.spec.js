import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import CartView from '@/views/cart/CartView.vue'

const mockCartStore = {
  items: ref([]),
  loading: ref(false),
  selectedCount: ref(0),
  selectedTotal: ref(0),
  fetchCart: vi.fn(),
  updateQuantity: vi.fn(),
  toggleItemSelect: vi.fn(),
  toggleAllSelected: vi.fn(),
  removeCartItem: vi.fn(),
}

vi.mock('@/stores/cart', () => ({
  useCartStore: () => mockCartStore,
}))

vi.mock('@/stores/loginGate', () => ({
  requireLogin: vi.fn().mockResolvedValue(true),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

describe('CartView', () => {
  beforeEach(() => {
    mockCartStore.items.value = []
    mockCartStore.selectedCount.value = 0
    mockCartStore.loading.value = false
  })

  it('shows empty state when no items', () => {
    const wrapper = mount(CartView)
    expect(wrapper.find('.empty-cart').exists()).toBe(true)
  })

  it('renders cart items when present', async () => {
    mockCartStore.items.value = [
      {
        id: 1,
        product: 10,
        quantity: 2,
        selected: true,
        product_detail: { id: 10, name: '购物车商品', price: '20.00', image: '' },
      },
    ]
    mockCartStore.selectedCount.value = 1
    const wrapper = mount(CartView)
    expect(wrapper.text()).toContain('购物车商品')
  })
})
