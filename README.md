# 校灵通（XLT）

> 面向校园场景的智能问答与知识管理系统，支持混合检索、角色权限管理和多知识库隔离。

## 项目简介

校灵通使用 FastAPI 和 Vue 3 构建，问答链路结合 ChromaDB 向量检索、Elasticsearch BM25 检索和 Rerank 重排，并通过角色关联控制用户可访问的知识库。

## 技术栈

- **后端**：FastAPI、Uvicorn、Pydantic 2、MySQL、ChromaDB、Elasticsearch 8.x
- **前端**：Vue 3、Vite、Element Plus、Vue Router 4、Pinia 4
- **AI 服务**：SiliconFlow 对话、向量化和精排模型
- **认证与存储**：JWT、Argon2id、阿里云 OSS
- **文档处理**：Markdown、TXT、PDF、DOCX

## 核心功能

- 混合检索问答：向量检索、BM25 召回、Rerank 精排、问题重写和流式回答
- 知识库管理：知识库创建、文档解析、文本切片、向量化和索引同步
- 权限管理：用户、角色和知识库关联，支持只读和读写权限
- 会话管理：多会话切换、历史保存、重命名和删除
- 公告系统：公告发布、附件上传和置顶
- 校园知识工作台：用户端、管理端和聊天端的统一界面与移动端适配

详细功能、项目结构和检索流程见[架构与功能说明](docs/架构与功能.md)。

## 快速开始

### 环境要求

- Python >= 3.11
- Node.js `^22.18.0` 或 `>=24.12.0`
- MySQL
- Elasticsearch 8.x，并安装 IK 中文分词插件
- uv
- 可访问的 SiliconFlow API
- 阿里云 OSS Bucket

### 1. 安装依赖

在项目根目录安装后端依赖：

```bash
uv sync
```

在 `frontend/` 目录安装前端依赖：

```bash
cd frontend
npm install
```

### 2. 配置环境变量

在项目根目录复制 `.env.example` 为 `.env`，填写数据库、Elasticsearch、AI 服务和 OSS 配置：

```powershell
Copy-Item .env.example .env
```

环境变量说明、模型配置和提示词约定见[配置与数据库说明](docs/配置与数据库.md)。`.env` 不应提交到版本库。

### 3. 初始化数据库

登录 MySQL 后执行：

```text
SOURCE sql/db.sql;
```

`sql/db.sql` 仅用于空环境首次初始化；已有数据库应按[配置与数据库说明](docs/配置与数据库.md)执行增量迁移。`sql/reset-dev.sql` 会删除整个 `xlt` 数据库，只能用于可丢弃全部数据的本地开发环境。

### 4. 启动服务

在项目根目录启动后端：

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

在另一个终端启动前端：

```bash
cd frontend
npm run dev
```

前端地址：<http://127.0.0.1:5173>

后端 Swagger UI：<http://127.0.0.1:8000/docs>

Windows 用户完成配置后也可以双击根目录的 `start.bat` 一键启动前后端。

### 默认账号

| 用户名 | 密码 | 类型 |
| --- | --- | --- |
| `admin` | `123456` | 管理员 |
| `hajimi` | `123456` | 普通用户 |

默认账号仅适合本地开发，请勿用于生产环境。

## 文档

- [架构与功能说明](docs/架构与功能.md)：项目结构、技术栈细节、核心功能、数据库概览和混合检索流程
- [配置与数据库说明](docs/配置与数据库.md)：环境变量、AI 配置、提示词、数据库初始化和数据迁移
- [API 与聊天协议](docs/API与聊天协议.md)：接口模块、鉴权约定、聊天 NDJSON 流和接口文档生成
- [开发与部署说明](docs/开发与部署.md)：测试、文件限制、安全要求、部署和外部服务一致性注意事项
- [接口文档](docs/接口文档.md)：由 `scripts/generate_api_doc.py` 生成的接口摘要

## 开发

后端测试：

```bash
uv sync --group dev
uv run pytest -q
```

前端生产构建：

```bash
cd frontend
npm run build
```

开发约定、安全边界和验证要求见根目录的 `AGENTS.md`。
