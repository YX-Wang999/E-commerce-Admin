import { config } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'

const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  messages: {
    'zh-CN': {
      auth: {
        phoneRequired: '请输入手机号',
        passwordRequired: '请输入密码',
        accountRequired: '请输入账号',
      },
      common: { noImage: '无图', loading: '加载中' },
      product: { platformShop: '平台自营', tagSubsidy: '国补', soldCount: '已售 {count}' },
      cart: {
        emptyTitle: '购物车空空如也',
        removeConfirmTitle: '确认删除',
        removeConfirmMessage: '确定删除该商品吗？',
        removed: '已删除',
        selectAtLeastOne: '请至少选择一件商品',
      },
    },
  },
})

config.global.plugins = [i18n]

config.global.stubs = {
  'van-image': { template: '<img />' },
  'van-button': { template: '<button><slot /></button>' },
  'van-checkbox': { template: '<input type="checkbox" />' },
  'van-stepper': { template: '<input type="number" />' },
  'van-empty': { template: '<div class="van-empty"><slot /></div>' },
  'van-loading': { template: '<div class="van-loading"><slot /></div>' },
  'van-submit-bar': { template: '<div class="van-submit-bar"><slot /></div>' },
  ProductPromoTags: true,
  AuthShell: { template: '<div><slot /></div>' },
  AuthPhoneField: { template: '<input />' },
  LocaleSwitcher: true,
}
