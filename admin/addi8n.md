# 国际化扩展指南（addi8n）

本文档说明本项目前端 i18n 架构，以及如何新增第四种及后续语言。

---

## 一、当前状态

| 语言代码 | 语言包 | Element Plus | 状态 |
|:---|:---|:---|:---|
| `zh-CN` | `src/i18n/locales/zh-CN.js` | `locale/zh-cn.mjs` | 默认语言、回退语言 |
| `en-US` | `src/i18n/locales/en-US.js` | `locale/en.mjs` | 已接入 |
| `ja-JP` | `src/i18n/locales/ja-JP.js` | `locale/ja.mjs` | 已接入 |

持久化键：`localStorage.admin_locale`

---

## 二、目录与职责

```
src/i18n/
├── index.js                 # createI18n、LOCALE_OPTIONS、翻译辅助函数
├── menu.js                  # resolveMenuLabel、pathToMenuKey、兜底逻辑
└── locales/
    ├── zh-CN.js             # 基准语言包（key 结构的唯一参照）
    ├── en-US.js
    └── ja-JP.js

src/router/
├── index.js                 # 路由定义，meta.i18nKey 与 i18nRegistry 同步
└── i18nRegistry.js          # path -> i18nKey 集中注册表

scripts/check-i18n-routes.mjs  # npm run check:i18n 校验脚本

src/stores/locale.js         # 语言切换、Element Plus locale、<html lang>
src/layout/components/SidebarMenu.vue   # 侧边栏（useMenuTitle）
src/assets/base.css          # .table-actions 多语言按钮对齐
```

### 核心配置一览

| 配置项 | 文件 | 说明 |
|:---|:---|:---|
| `LOCALE_OPTIONS` | `i18n/index.js` | 语言切换下拉选项 |
| `messages` | `i18n/index.js` | 注册各语言包 |
| `getInitialLocale()` | `i18n/index.js` | localStorage + 浏览器语言检测 |
| `ELEMENT_LOCALE_MAP` | `stores/locale.js` | Element Plus 组件库语言 |
| `HTML_LANG_MAP` | `stores/locale.js` | `document.documentElement.lang` |

---

## 三、新增语言：必改 4 处

以新增 **韩语 `ko-KR`** 为例，按顺序完成以下修改。

### 3.1 新建语言包

```powershell
cd admin
copy src\i18n\locales\en-US.js src\i18n\locales\ko-KR.js
```

**规则：**

- key 结构与 `zh-CN.js` 完全一致，只翻译 value
- 不可删改 key 名
- 推荐以 `en-US.js` 复制后翻译（已是完整结构）

### 3.2 所有已有语言包的 `locale` 段

每个语言包中的 `locale` 必须包含**全部已支持语言**的显示名：

```javascript
locale: {
  label: '...',       // 当前语言下「语言」一词
  zhCN: '简体中文',
  enUS: 'English',
  jaJP: '日本語',
  koKR: '한국어',     // 新增项
},
```

需同步修改：`zh-CN.js`、`en-US.js`、`ja-JP.js`、`ko-KR.js`（共 N+1 个文件）。

### 3.3 注册到 `src/i18n/index.js`

```javascript
import koKR from '@/i18n/locales/ko-KR'

export const LOCALE_OPTIONS = [
  { value: 'zh-CN', labelKey: 'locale.zhCN' },
  { value: 'en-US', labelKey: 'locale.enUS' },
  { value: 'ja-JP', labelKey: 'locale.jaJP' },
  { value: 'ko-KR', labelKey: 'locale.koKR' },  // 新增
]

function getInitialLocale() {
  const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (saved && ['zh-CN', 'en-US', 'ja-JP', 'ko-KR'].includes(saved)) {
    return saved
  }
  const browserLang = navigator.language
  if (browserLang.startsWith('ko')) return 'ko-KR'
  if (browserLang.startsWith('ja')) return 'ja-JP'
  if (browserLang.startsWith('en')) return 'en-US'
  return DEFAULT_LOCALE
}

const i18n = createI18n({
  // ...
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
    'ja-JP': jaJP,
    'ko-KR': koKR,  // 新增
  },
})
```

> `FALLBACK_LOCALE` 保持 `zh-CN`：缺失 key 时回退中文。

### 3.4 注册到 `src/stores/locale.js`

```javascript
import ko from 'element-plus/dist/locale/ko.mjs'

const ELEMENT_LOCALE_MAP = {
  'zh-CN': zhCn,
  'en-US': enUS,
  'ja-JP': ja,
  'ko-KR': ko,  // 新增
}

const HTML_LANG_MAP = {
  'zh-CN': 'zh-CN',
  'en-US': 'en',
  'ja-JP': 'ja',
  'ko-KR': 'ko',  // 新增
}
```

Element Plus 内置语言见：[Element Plus 国际化](https://element-plus.org/zh-CN/guide/i18n.html)。若无对应包，可临时映射到 `enUS`。

---

## 四、语言包命名空间

| 命名空间 | 用途 | 是否必须完整 |
|:---|:---|:---|
| `common` | 通用按钮、提示 | 是 |
| `locale` | 语言切换器名称 | 是 |
| `menu` | 目录级菜单（约定式 key） | 是，仅父级目录 |
| `menuByPath` | 侧边栏菜单（按 path，兼容旧逻辑） | 逐步废弃，保留兜底 |
| `layout` | 顶栏退出、改密 | 是 |
| `login` / `activate` / `password` | 登录流程 | 是 |
| `dashboard.cards` | 仪表盘卡片（API key 映射） | 是 |
| `inventoryType` | 库存变动类型 | 是 |
| `product` / `order` / `customer` / `report` | 业务页 | 是 |
| `system.*` | 系统管理 | 是 |

---

## 五、侧边栏菜单 i18n（推荐工作流）

后端返回的菜单 `title` 为中文，前端通过 **path** 翻译。侧边栏使用 `useMenuTitle()`（`SidebarMenu.vue`），切换语言时会响应式更新。

### 5.1 解析优先级（`resolveMenuLabel`）

| 优先级 | 来源 | 示例 |
|:---|:---|:---|
| 1 | `src/router/i18nRegistry.js` | `/products/list` → `product.listTitle` |
| 2 | 约定式 `menu.{path_key}` | `/products` → `menu.products` |
| 3 | 兼容旧版 `menuByPath.{path}` | `/products/list` → `menuByPath['/products/list']` |
| 4 | 路径段兜底 | `/foo/bar-baz` → `Bar Baz` |
| 5 | 后端中文 title | API 返回值 |

### 5.2 新增路由 checklist（只需 2 步）

**步骤 A — 注册 i18n key**（`src/router/i18nRegistry.js`）：

```javascript
export const ROUTE_I18N_KEYS = {
  '/your/new-page': 'yourModule.listTitle',  // 复用页面标题 key
  '/your-module': 'menu.your_module',         // 目录级用 menu.*
}
```

**步骤 B — 路由 meta**（`src/router/index.js`）：

```javascript
{
  path: 'your/new-page',
  meta: { i18nKey: 'yourModule.listTitle' },
  component: () => import('@/views/your/NewPage.vue'),
}
```

**步骤 C — 语言包**：在 `zh-CN.js` / `en-US.js` / `ja-JP.js` 添加 `yourModule.listTitle`（页面 key 通常已有）。目录级菜单只需维护 `menu.your_module` 三语。

**步骤 D — 校验**：

```powershell
npm run check:i18n
```

> 叶子路由优先复用页面 `listTitle` / `title`，避免与 `menuByPath` 重复维护。`menuByPath` 保留作兼容，新路由不必再添加。

### 5.3 目录 path 列表（仅 `menu.*` 需三语维护）

| path | menu key |
|:---|:---|
| `/dashboard` | `menu.dashboard` |
| `/products` | `menu.products` |
| `/promotions` | `menu.promotions` |
| `/orders` | `menu.orders` |
| `/customers` | `menu.customers` |
| `/reports` | `menu.reports` |
| `/reports/overview` | `menu.reports_overview` |
| `/system` | `menu.system` |

叶子菜单 path 见 `i18nRegistry.js`，通常复用 `product.listTitle` 等业务 key。

### 5.4 组件内用法

```javascript
import { useMenuTitle } from '@/i18n'

const translateMenuTitle = useMenuTitle()
// translateMenuTitle(item.path, item.title)
```

不要在 `setup` 中直接使用 `translateMenuTitle()`（非响应式）；应使用 `useMenuTitle()`。

---

## 六、后端数据映射

以下字段来自 API，前端通过 key 映射翻译：

| 映射函数 | 语言包路径 | 使用位置 |
|:---|:---|:---|
| `useMenuTitle()` | `i18nRegistry` → `menu.*` → `menuByPath.*` | 侧边栏、菜单管理父级选择 |
| `translateDashboardCard()` | `dashboard.cards.*` | 仪表盘卡片 |
| `translateInventoryType()` | `inventoryType.*` | 商品库存流水 |
| `translateActivationStatus()` | `system.user.activationStatus*` | 用户激活状态 |

新增语言时，以上段落必须完整翻译。新增路由时，更新 `i18nRegistry.js` + 路由 `meta.i18nKey`，运行 `npm run check:i18n` 校验。

---

## 七、表格操作列对齐

长文案（英/日/韩/俄）会导致 link 按钮换行错位。使用 `src/assets/base.css` 中的 `.table-actions` 固定槽位，参考 `ProductList.vue`。

| 类名 | min-width | 用途 |
|:---|:---|:---|
| `table-actions__slot--md` | 5rem | 删除 |
| `table-actions__slot--edit` | 7.5rem | 编辑 |
| `table-actions__slot--lg` | 8rem | 库存流水 |
| `table-actions__slot--sale` | 10rem | 上架/下架（共用槽位） |

上架/下架应放在**同一槽位**内用 `v-if` / `v-else` 切换，避免行间删除按钮左右跳动。

---

## 八、页面开发规范

### 模板与脚本

```vue
<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const rules = computed(() => ({
  name: [{ required: true, message: t('product.nameRequired'), trigger: 'blur' }],
}))
</script>

<template>
  <span>{{ t('product.listTitle') }}</span>
</template>
```

### ECharts 图表

监听 `locale` 变化后重绘，参考 `DashboardView.vue`、`ReportView.vue`：

```javascript
const { t, locale } = useI18n()
watch(locale, () => loadChart())
```

---

## 九、ja-JP 接入回顾

日语已完成接入，可作为后续语言的参照样本。

| 步骤 | 文件 | 状态 |
|:---|:---|:---|
| 语言包 | `locales/ja-JP.js` | 已完成 |
| 注册 messages | `i18n/index.js` | 已完成 |
| Element Plus | `stores/locale.js` → `ja.mjs` | 已完成 |
| HTML lang | `stores/locale.js` → `HTML_LANG_MAP` | 已完成 |
| 各语言包 `locale.jaJP` | zh-CN / en-US / ja-JP | 已完成 |
| 父级目录 `menuByPath` | ja-JP.js | 已补全 |

---

## 十、验证清单

```
[ ] 新建 locales/xx-XX.js，key 与 zh-CN.js 一致
[ ] 所有语言包 locale 段增加新语言名称
[ ] i18n/index.js：import、messages、LOCALE_OPTIONS、getInitialLocale 白名单
[ ] stores/locale.js：ELEMENT_LOCALE_MAP、HTML_LANG_MAP
[ ] menu 段含全部 8 个目录 key
[ ] i18nRegistry.js 与 router meta.i18nKey 一致
[ ] npm run check:i18n 通过
[ ] dashboard.cards / inventoryType / system.user.activationStatus* 已翻译
[ ] 顶栏、登录页语言下拉出现新选项
[ ] 切换语言后侧边栏即时更新（无需刷新）
[ ] 切换后刷新，localStorage.admin_locale 仍保留
[ ] Element Plus 分页、日期组件语言正确
[ ] npm run build 通过
```

```powershell
cd admin
npm run dev
npm run build
```

---

## 十一、常见问题

**Q：切换语言后某处仍是中文？**

1. 该文案是否硬编码在 `.vue` 中（未用 `t()`）
2. 新语言包是否缺少 key（回退到 `zh-CN`）
3. 是否为 API 返回字段（`message`、审计模块名等），需前端按 code 映射或后端多语言

**Q：侧边栏目录名仍是中文，子菜单已翻译？**

检查 `menu.products` 等目录 key 是否在三语包 `menu` 段中维护；或 `i18nRegistry.js` 是否遗漏该 path。

**Q：切换语言后侧边栏不更新？**

确认使用 `useMenuTitle()`，而非 `translateMenuTitle()`。

**Q：Element Plus 组件仍是英文？**

确认 `ELEMENT_LOCALE_MAP` 已注册，且 `App.vue` 使用 `<el-config-provider :locale="elementLocale">`。

**Q：语言包按需加载？**

当前 3 语言同步 import 即可。语言增多时可改为：

```javascript
async function loadLocale(code) {
  const mod = await import(`./locales/${code}.js`)
  i18n.global.setLocaleMessage(code, mod.default)
}
```

---

## 十二、快速检查表（Copy Checklist）

新增 `xx-XX` 时复制使用：

```
[ ] copy en-US.js → xx-XX.js，翻译全部 value
[ ] zh-CN / en-US / ja-JP / xx-XX 的 locale 段增加 locale.xxXX
[ ] i18n/index.js 四处：import、LOCALE_OPTIONS、getInitialLocale、messages
[ ] locale.js 两处：ELEMENT_LOCALE_MAP、HTML_LANG_MAP
[ ] menu 段 8 个目录 key 全部翻译
[ ] i18nRegistry.js + router meta.i18nKey 已同步
[ ] npm run check:i18n && npm run build && 浏览器切换验证
```

---

*路径：`admin/addi8n.md` · 基准语言包：`src/i18n/locales/zh-CN.js`*
