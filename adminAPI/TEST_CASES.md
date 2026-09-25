# 测试用例清单

> 自动化测试：`accounts/tests.py`、`products/tests.py`、`orders/tests.py`、`points/tests.py`  
> 前端：`customer/src/__tests__/` · E2E：`e2e/customer-flow.spec.js`  
> 种子数据：`python manage.py seed_test_data --users=10 --products=20 --orders=30`

## 覆盖率目标

| 层级 | 目标 | 说明 |
|:---|:---:|:---|
| 后端 API | 80% | 核心业务逻辑 |
| 前端组件 | 60% | 关键页面和组件 |
| E2E 关键路径 | 100% | 主流程全覆盖 |
| 工具函数 | 100% | 纯函数 |

## 认证模块

| 模块 | 测试场景 | 前置条件 | 操作步骤 | 预期结果 |
|:---|:---|:---|:---|:---|
| 认证 | 登录成功 | 有效用户 | POST `/api/auth/login/` | code=0，返回 token |
| 认证 | 密码错误 | 有效用户 | 错误密码 | code=40007 |
| 认证 | 用户不存在 | - | 不存在用户名 | code=40006 |
| 认证 | 首次登录改密 | is_first_login | 登录 | code=1001 |
| 认证 | Token 刷新 | 有效 refresh | POST `/api/auth/refresh/` | 新 access |
| 认证 | 修改密码 | 已登录 | change-password | 成功 |
| 认证 | 验证码 | - | captcha + verify | 通过 |

## 商品 / 订单 / 积分 API

| 模块 | 测试场景 | 前置条件 | 操作步骤 | 预期结果 |
|:---|:---|:---|:---|:---|
| 商品 | 公开列表 | 有上架商品 | GET `/api/products/` | 不含下架 |
| 商品 | 详情不存在 | - | GET 无效 id | 404 |
| 商品 | 无权限创建 | 未登录 | POST | 401 |
| 商品 | 管理员创建 | admin token | POST | 成功 |
| 订单 | 正常下单 | 客户+地址+库存 | POST checkout | 成功扣库存 |
| 订单 | 库存不足 | stock=0 | POST | 失败提示 |
| 订单 | 只看自己订单 | 两客户各有订单 | GET list | 仅本人 |
| 订单 | 取消待付款 | pending | POST cancel | cancelled |
| 订单 | 已发货不可取消 | shipped | POST cancel | 拒绝 |
| 积分 | 首次签到 | 规则启用 | POST sign-in | 积分+ |
| 积分 | 重复签到 | 当日已签 | 再签 | 今日已签到 |
| 积分 | 流水分页 | 有流水 | GET transactions | 分页正确 |

## 通知完成状态

| 模块 | 状态 |
|:---|:---:|
| 订单通知 | ✅ |
| 售后通知 | ✅ |
| 审核通知 | ✅ |
| 商户入驻通知 | ✅ |
| 库存通知 | 部分 |
| 促销通知 | 待接入 |
| 投诉通知 | ✅ |

## 运行命令

```bash
cd adminAPI && python manage.py test accounts.tests products.tests orders.tests points.tests
cd adminAPI && python manage.py seed_test_data
cd customer && npm install && npm run test
npx playwright test
```
