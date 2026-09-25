import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ProductCard from '@/components/product/ProductCard.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

describe('ProductCard', () => {
  const product = {
    id: 1,
    name: '测试商品A',
    price: '99.90',
    image: '/media/test.jpg',
    promo_tags: [{ code: 'new', name: '新品', color: '#333', text_color: '#fff' }],
  }

  it('renders product name and price', () => {
    const wrapper = mount(ProductCard, { props: { product } })
    expect(wrapper.text()).toContain('测试商品A')
    expect(wrapper.text()).toContain('99.90')
  })

  it('emits click when card clicked', async () => {
    const wrapper = mount(ProductCard, { props: { product } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')?.[0]?.[0]).toEqual(product)
  })
})
