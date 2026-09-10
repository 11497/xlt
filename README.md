# 校灵通（XLT）

> 面向校园场景的智能问答与知识管理系统，支持混合检索、角色权限管理和多知识库隔离。

## 项目简介

校灵通使用 FastAPI 和 Vue 3 构建，问答链路结合 ChromaDB 向量检索、Elasticsearch BM25 检索和 Rerank 重排，并通过角色关联控制用户可访问的知识库。

## 技术栈

- **后端**：FastAPI、Uvicorn、Pydantic 2、MySQL、ChromaDB、Elasticsearch 8.x
- **前端**：Vue 3、Vite、Element Plus、Vue Router 4、Pinia 4
- **AI 服务**：对话、向量化和精排模型（当前默认 SiliconFlow，地址与模型名在 `config/ai_config.py`）
- **认证与存储**：JWT、Argon2id、阿里云 OSS
- **文档处理**：Markdown、TXT、PDF、DOCX

## 核心功能

- 混合检索问答：向量检索、BM25 召回、Rerank 精排、问题重写和流式回答
- 回答来源溯源：保存生成时使用的来源快照，可在聊天页及用户端、管理端的会话详情中查看
- 知识库管理：知识库创建、文档异步解析、文本切片、向量化和索引同步（状态可查询、失败可重试）
- 权限管理：用户、角色和知识库关联，支持只读和读写权限
- 会话管理：多会话切换、历史保存、重命名和逻辑删除
- 公告系统：公告发布、附件上传、置顶和逻辑删除
- 删除语义：业务数据逻辑删除，文档/知识库检索索引真实删除，OSS 对象保留；细节见[架构与功能说明](docs/架构与功能.md)
- 校园知识工作台：用户端、管理端和聊天端的统一界面与移动端适配

详细功能、项目结构、异步索引和检索流程见[架构与功能说明](docs/架构与功能.md)。

## 快速开始

### 环境要求

- Python >= 3.11
- Node.js `^22.18.0` 或 `>=24.12.0`
- MySQL
- Elasticsearch 8.x，并安装 IK 中文分词插件
- uv
- 可访问的对话、向量化和精排 API（当前默认 SiliconFlow）
- 阿里云 OSS（`.env` 填密钥；Bucket 与 Endpoint 在 `config/oss_config.py`）

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

在项目根目录复制 `.env.example` 为 `.env`，填写数据库、Elasticsearch、AI 密钥和 OSS 密钥：

```powershell
Copy-Item .env.example .env
```

环境变量说明、模型配置和提示词约定见[配置与数据库说明](docs/配置与数据库.md)。`.env` 不应提交到版本库。

### 3. 初始化数据库

登录 MySQL 后执行：

```text
SOURCE sql/db.sql;
```

`sql/db.sql` 仅用于空环境首次初始化。重置方式、软删除字段和注意事项见[配置与数据库说明](docs/配置与数据库.md)。

### 4. 启动服务

在项目根目录启动后端：

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

在另一个终端启动文档异步 Worker（文档索引/删除依赖它，否则文档会停留在待索引状态）：

```bash
uv run python -m ai.indexing_worker
```

可选：定期对账服务（恢复卡死任务、核对索引；不删除 OSS 对象）：

```bash
uv run python -m ai.reconciliation_service
```

在另一个终端启动前端：

```bash
cd frontend
npm run dev
```

前端地址：<http://127.0.0.1:5173>

后端 Swagger UI：<http://127.0.0.1:8000/docs>

Windows 用户完成配置后也可以双击根目录的 `start.bat` 一键启动前后端（会同时启动后端、文档索引 Worker 和前端；对账服务默认不启动，可按需启用）。

### 默认账号

| 用户名 | 密码 | 类型 |
| --- | --- | --- |
| `admin` | `123456` | 管理员 |
| `hajimi` | `123456` | 普通用户 |

默认账号仅适合本地开发，请勿用于生产环境。

## 文档

- [架构与功能说明](docs/架构与功能.md)：项目结构、核心功能、数据库概览、异步索引和检索流程
- [配置与数据库说明](docs/配置与数据库.md)：环境变量、AI 配置、提示词、数据库初始化和常见问题
- [API 与聊天协议](docs/API与聊天协议.md)：接口模块、鉴权约定、聊天 NDJSON 流和接口文档生成
- [开发与部署说明](docs/开发与部署.md)：测试、文件限制、安全要求、部署和外部服务一致性注意事项
- [接口文档](docs/接口文档.md)：由 `scripts/generate_api_doc.py` 生成的接口摘要

## 开发

后端测试：

```bash
uv sync --group dev
uv run pytest -q
```

恢复单个已删除文档的索引（人工维护，先在 `scripts/restore_deleted_document.py` 顶部填写文档 ID）：

```bash
uv run python scripts/restore_deleted_document.py
uv run python scripts/restore_deleted_document.py --execute
```

默认命令只核验并输出恢复目标摘要；`--execute` 才会下载 OSS 留存对象、重建 ChromaDB/Elasticsearch 索引并恢复文档状态。
执行 `--execute` 前必须暂停文档索引 Worker 和对账服务，恢复完成后再重新启动；否则独立进程可能与脚本同时操作目标索引。脚本仍会在执行前和最终落库前检查活动任务，但该检查不能替代暂停进程。

前端生产构建：

```bash
cd frontend
npm run build
```

开发约定、安全边界和验证要求见根目录的 `AGENTS.md`。
