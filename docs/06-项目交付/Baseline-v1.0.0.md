# 电商管理平台 — Baseline v1.0.0

> **基线说明**  
> 本文档记录截至 **v1.0.0** 的完整交付成果，涵盖 **管理后台（admin）**、**商城（customer）**、**商家后台（seller）** 与 **统一 API（adminAPI）**。  
> 后续迭代请在新版本文档中用 Added / Changed / Deprecated / Removed 标注相对本基线的差异。  
> 文档体系入口：[docs/README.md](../README.md)

---

## 1. 项目概览

| 子项目 | 路径 | 端口（开发） | 说明 |
|--------|------|--------------|------|
| 管理后台 | `admin/` | 5173 | Vue 3 + Element Plus，内部员工 RBAC |
| 商城前台 | `customer/` | 5174 | Vue 3 + Vant，C 端购物与会员 |
| 商家后台 | `seller/` | 5175 | Vue 3 + Element Plus，店铺经营 |
| 后端 API | `adminAPI/` | 8000 | Django REST + Channels（Daphne） |

**核心架构原则**：

- **员工（User）** 与 **商城用户（Customer）** 数据分离。
- JWT 双轨：`CustomerJWTAuthentication` / SimpleJWT。
- 统一响应：`{ "code": 0, "data": {}, "message": "success" }`。

（以下章节与 `admin/Baseline-v1.0.0.md` 同步；启动后端请使用 `run-dev.bat` / Daphne 以支持 WebSocket。）

---

## 2～10. 详细基线内容

完整技术基线（认证、API 摘要、角色矩阵、迁移、已知限制等）见同源文件：

**[admin/Baseline-v1.0.0.md](../../admin/Baseline-v1.0.0.md)**

### v1.0.0 相对 Baseline 原文的补充交付

| 类别 | 项 |
|------|-----|
| Added | 商家端 seller/、统一审核 approval、标签系统、国补、店铺评分/注销、WebSocket 通知与导航红点 |
| Added | `docs/` 完整文档体系 |
| Changed | 后端 ASGI 必须用 Daphne；三端 + shared 热加载通知 |
| Docs | [架构设计](../02-开发人员专用/架构设计.md)、[接口文档](../02-开发人员专用/接口文档.md) |

---

## 版本信息

| 项 | 值 |
|----|-----|
| 版本号 | **v1.0.0** |
| 基线日期 | 2026-06-27 |
| 文档性质 | Baseline（四端一体） |

---

*Baseline v1.0.0 — 电商管理后台 + 商城 + 商家 + 统一 API*
