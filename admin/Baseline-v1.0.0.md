# 电商管理平台 — Baseline v1.0.0

> **基线说明**  
> 本文档记录截至 **v1.0.0** 的完整交付成果，涵盖 **管理后台（admin）**、**商城前台（customer）** 与 **统一 API（adminAPI）**。  
> 后续迭代请在新版本文档中用 Added / Changed / Deprecated / Removed 标注相对本基线的差异。

---

## 1. 项目概览

| 子项目 | 路径 | 端口（开发） | 说明 |
|--------|------|--------------|------|
| 管理后台 | `admin/` | 5173 | Vue 3 + Element Plus，内部员工 RBAC |
| 商城前台 | `customer/` | 5174 | Vue 3 + Vant，C 端购物与会员 |
| 后端 API | `adminAPI/` | 8000 | Django REST，统一服务两端 |

**核心架构原则**：

- **员工（User）** 与 **商城用户（Customer）** 数据分离：后台登录走 `accounts.User`，商城注册/登录走 `customers.Customer`。
- JWT 双轨：`CustomerJWTAuthentication` 识别 `customer_id` 声明；SimpleJWT 识别后台 `user_id`。
- 统一响应：`{ "code": 0, "data": {}, "message": "success" }`；未捕获异常 → `code: 50000`。

### 1.1 技术栈

| 层级 | 管理后台 | 商城 | 后端 |
|------|----------|------|------|
| 框架 | Vue 3.5、Vite 8 | Vue 3.5、Vite 8 | Django 4.2、DRF、SimpleJWT |
| UI | Element Plus 2.14 | Vant 4 | — |
| 状态 / 路由 | Pinia、Vue Router 5 | Pinia、Vue Router 5 | — |
| 国际化 | vue-i18n（zh/en/ja） | vue-i18n（zh/en/ja） | — |
| 其他 | ECharts 6 | vue-tel-num-input、libphonenumber-js | Channels、阿里云短信 SDK |

### 1.2 业务码（常用）

| code | 含义 |
|------|------|
| `0` | 成功 |
| `1001` | 后台首次登录，需改密 |
| `40002` | 商城：用户名/手机号或密码错误 |
| `40011`–`40014` | 商城短信相关错误 |
| `40100` | Token 无效 |
| `40300` | 无权限 |
| `50000` | 服务器内部错误 |

---

## 2. 身份与认证

### 2.1 后台员工（accounts.User）

- 登录：`POST /api/auth/login/`（用户名 + 密码；按信任等级决定是否需要 SliderCaptcha）
- 滑块验证：[ArgoZhang/SliderCaptcha](https://github.com/ArgoZhang/SliderCaptcha) 风格拼图，**按风险分级触发**：
  - **高信任**：常用设备/IP，登录无感，不出现滑块
  - **中风险**：点击登录后，服务端返回 `40005` + 拼图数据，弹窗内完成滑块（先操作后验证）
  - **低信任**：页面显示「点击开始验证」，须先完成滑块再登录（操作前强制验证）
- 信任评估：`GET /api/auth/captcha/trust/`；设备指纹 `X-Device-Id` / `device_id`
- 找回密码：邮箱链接（QQ SMTP），与账号激活共用 Token 体系
- 角色：9 个 RBAC 角色，动态菜单树

### 2.2 商城用户（customers.Customer）

- **注册**：手机号（E.164）+ 短信验证码 + 密码
- **登录**：用户名或手机号 + 密码（支持昵称、邮箱、11 位国内号、E.164）
- **找回密码**：手机号 + 短信验证码（**独立短信模板**，见 §4.3）
- JWT：`CustomerRefreshToken` 含 `customer_id`、`token_type=customer`

### 2.3 短信场景与模板对照

| 场景 | scene 值 | 参考示例工程 | 默认签名 | 默认模板 CODE |
|------|----------|--------------|----------|---------------|
| 注册 | `register` | `API/API-Python` | 速通互联验证码 | `100001` |
| 找回密码 | `reset_password` | `API/ChangepwdAPITemp-Python` | 云渚科技验证平台 | `100003` |

实现位置：`adminAPI/customers/sms_service.py` → `_resolve_sms_template(scene)`。

发送：`SendSmsVerifyCode`（`return_verify_code=True`）。校验：本地库 + 阿里云 `CheckSmsVerifyCode` 双通道。

---

## 3. 后端结构（adminAPI/）

```
adminAPI/
├── config/              # settings、urls、JWT、CORS、双短信模板 env
├── common/              # 响应、分页、异常、上传
├── accounts/            # 后台 User、SliderCaptcha 滑块验证、激活/邮件找回
│   ├── slider_captcha.py
│   ├── captcha_trust.py   # 高/中/低信任分级
│   └── captcha_images/    # SliderCaptcha 背景图 Pic0–Pic4
├── customers/           # 商城 Customer、短信、JWT 认证、商城 auth API
│   ├── sms_service.py   # 按 scene 选模板
│   ├── auth_utils.py    # 用户名/手机号解析登录
│   └── authentication.py
├── rbac/ audit/ system/ # RBAC、审计、系统配置（含角色显示名）
├── products/ orders/    # 商品、订单（Customer 关联）
├── cart/ addresses/     # 购物车、收货地址（Customer FK）
├── points/ chat/        # 积分、客服会话
├── promotion/ reports/  # 促销、报表
├── announcement/        # 公告（商城用户仅看 scope=all）
└── requirements.txt     # 含 alibabacloud-dypnsapi20170525
```

### 3.1 Customer 模型（商城）

| 字段 | 说明 |
|------|------|
| phone | E.164，唯一，最长 32 |
| password | Django hash |
| nickname / name | 展示名，可登录 |
| email | 可选，可登录 |
| level / points | 会员等级与积分 |
| is_active | 禁用后不可登录 |

### 3.2 SystemSetting 扩展

- `role_display_names`：角色多语言显示名（zh-CN / en-US / ja-JP）
- API：`GET/PUT /api/system/settings/role-display-names/`
- 公开合并结果：`GET /api/system/settings/public/`（需登录）

---

## 4. 商城 API 清单（前缀 `/api/customers/`）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `auth/send-sms/` | 公开 | 发短信，`scene`: register / reset_password |
| POST | `auth/register/` | 公开 | 注册 |
| POST | `auth/login/` | 公开 | 登录，`account` + `password` |
| POST | `auth/refresh/` | 公开 | 刷新商城 token |
| POST | `auth/reset-password/` | 公开 | 短信重置密码 |
| GET/PATCH | `auth/profile/` | 商城 JWT | 个人资料 |
| CRUD | `/api/customers/` | 后台 | 会员管理（禁用/删除） |

**兼容别名**：`POST /api/send-sms/` → 同 `send-sms`。

### 4.1 商城前端认证页（customer/）

| 路径 | 说明 |
|------|------|
| `/login` | 用户名/手机号 + 密码，`AuthShell` 宽卡片（520px） |
| `/register` | 国际手机号 + 短信 + 密码 |
| `/forgot-password` | 手机号 + **重置密码短信模板** + 新密码 |

组件：`AuthShell.vue`、`AuthPhoneField.vue`、`PhoneTelInput.vue`（vue-tel-num-input）。

### 4.2 短信环境变量（adminAPI/.env）

```env
ALIBABA_CLOUD_ACCESS_KEY_ID=
ALIBABA_CLOUD_ACCESS_KEY_SECRET=

ALIYUN_SMS_ENABLED=False          # False=开发模式，响应带 dev_code
# 注册（API/API-Python）
ALIYUN_SMS_SIGN_NAME=速通互联验证码
ALIYUN_SMS_TEMPLATE_CODE=100001
# 找回密码（API/ChangepwdAPITemp-Python）
ALIYUN_SMS_RESET_SIGN_NAME=云渚科技验证平台
ALIYUN_SMS_RESET_TEMPLATE_CODE=100003
SMS_RESEND_SECONDS=10
```

`ALIYUN_SMS_ENABLED=True` 时需 `pip install -r requirements.txt` 并配置 AccessKey。

### 4.3 短信调用链（商城）

```
用户点击「获取验证码」
  → POST /api/customers/auth/send-sms/ { phone, scene }
  → sms_service.send_verification_code()
  → scene=register     → 模板 100001
  → scene=reset_password → 模板 100003
  → 阿里云 SendSmsVerifyCode → 入库 SmsVerificationCode
  → 注册/重置时 verify_code()（本地或 CheckSmsVerifyCode）
```

---

## 5. 管理后台 API 摘要

> 完整清单见历史章节；此处列 v1.0.0 关键路径。前缀 `/api/`。

| 模块 | 代表路径 |
|------|----------|
| 认证 | `/auth/login/`、`/auth/profile/`、`/auth/forgot-password/` |
| RBAC | `/permissions/`、`/roles/`、`/menus/` |
| 商品 | `/products/`、`/products/categories/` |
| 促销 | `/promotions/seckills/`、`/groupbuys/`、`/coupons/` |
| 订单 | `/orders/`、`/orders/refunds/` |
| 会员 | `/customers/`（后台 CRUD，与商城 Customer 同表） |
| 报表 | `/reports/dashboard/`、`/reports/sales/` |
| 系统 | `/system/settings/`、`/system/settings/role-display-names/` |
| 审计 | `/audit/logs/` |

### 5.1 后台前端（admin/）

- 登录：SliderCaptcha 滑块拼图 + 演示账号 + 邮箱找回密码
- 系统设置 Tab：**角色名称自定义**（`RoleNamesTab.vue` + `useRoleLabel`）
- 用户列表 / 角色 / 仪表盘等已接自定义角色显示名
- 路由守卫：`is_first_login` 强制改密；`fetchProfile` + `roleDisplayStore`

### 5.2 角色矩阵（9 角色）

| code | 演示账号 | 名称 |
|------|----------|------|
| super_admin | admin | 超级管理员 |
| ops_director | ops_director | 运营总监 |
| ops_manager | ops_manager | 运营主管 |
| ops_staff | ops_staff | 运营专员 |
| cs_staff | cs_staff | 客服专员 |
| warehouse_manager | warehouse | 仓库管理员 |
| data_analyst | data_analyst | 数据分析师 |
| dept_manager | dept_manager | 部门经理 |
| employee | employee | 普通员工 |

演示密码均为 `admin123456`。`python manage.py init_data` 初始化。

---

## 6. 环境与启动

### 6.1 后端

```powershell
cd adminAPI
pip install -r requirements.txt
copy .env.example .env    # 编辑 .env（勿提交 Git）
python manage.py migrate
python manage.py init_data
python manage.py runserver
```

### 6.2 管理后台

```powershell
cd admin
npm install
npm run dev    # http://localhost:5173
```

### 6.3 商城

```powershell
cd customer
npm install
npm run dev    # http://localhost:5174
```

Vite 代理：`/api` → `8000`。CORS 需包含 `5173` 与 `5174`。

### 6.4 常见问题

| 现象 | 处理 |
|------|------|
| 管理后台登录后 500 | 检查 `/api/system/settings/public/` 导入是否完整；重启 Django |
| 商城登录后 500 | 公告接口对 Customer 无 `roles` 已兼容；重启后端 |
| 短信「未收到验证码」但手机已收到 | 需 `ReturnVerifyCode=true`（已实现）；重启后端 |
| 找回密码短信失败 | 确认 `.env` 中 `ALIYUN_SMS_RESET_*` 与 Changepwd 模板一致 |
| SDK 报错 | `pip install -r requirements.txt` |

---

## 7. 数据库迁移（v1.0.0 增量）

| 应用 | 迁移 | 说明 |
|------|------|------|
| customers | 0002 | 商城 auth 字段 |
| customers | 0003 | phone E.164 扩位 |
| customers | 0004 | SmsVerificationCode.out_id |
| system | 0002 | role_display_names 种子 |
| cart / addresses | 0002 | user → customer FK 迁移 |
| points | 0003 | 积分账户回填 |

---

## 8. 参考工程（API/）

| 目录 | 用途 |
|------|------|
| `API/API-Python` | 注册短信 `SendSmsVerifyCode` 示例（100001） |
| `API/ChangepwdAPITemp-Python` | 找回密码短信示例（100003） |

生产配置以 `.env` 为准，示例工程仅作签名/模板 CODE 对照。

---

## 9. 已知限制与后续建议

| 类别 | 项 |
|------|-----|
| 商城 | 独立 username 字段（当前用 nickname/phone/email 登录） |
| 短信 | Celery 异步发送、IP/设备级限流 |
| 权限 | 按钮级 v-permission、部门经理数据域 |
| 部署 | Docker、Nginx、HTTPS |
| 测试 | 单元 / 集成测试覆盖 |

### v1.0.0 相对早期草案的主要交付

- **Added**：商城 Customer 体系、短信双模板、国际手机号、角色显示名自定义、积分/购物车/客服、商城宽版认证 UI
- **Changed**：Customer 与 User 分离；短信校验接阿里云 CheckSmsVerifyCode；登录支持用户名/手机号
- **Fixed**：商城登录后公告 500；短信 ReturnVerifyCode；管理后台 public settings 500

---

## 10. 版本信息

| 项 | 值 |
|----|-----|
| 版本号 | **v1.0.0** |
| 基线日期 | 2026-06-27 |
| 文档性质 | Baseline（三端一体） |

---

*Baseline v1.0.0 — 电商管理后台 + 商城前台 + 统一 API*
