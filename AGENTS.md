# AGENTS.md

## 项目概况

- 本项目是校园知识库问答与管理系统，后端使用 Python 3.11+、FastAPI 和 PyMySQL，前端使用 Vue 3、Vite、Element Plus 和 npm。
- 后端依赖使用 `uv` 和 `pyproject.toml`/`uv.lock` 管理；前端依赖使用 `frontend/package.json`/`frontend/package-lock.json` 管理。
- AI、向量化和精排服务均通过 `config/ai_config.py` 配置，业务代码不得硬编码模型供应商、服务地址或密钥。
- 集成验证可能依赖数据库、检索服务、对象存储和模型服务；未经明确授权，不连接或修改真实外部服务。
- ChromaDB 本地数据位于根目录 `chroma_db/`，不得提交。
- 先阅读相关模块及 `README.md`，沿用现有分层和命名，不进行与当前任务无关的重构。
- 所有文本文件使用 UTF-8；代码注释、接口消息和项目文档默认使用中文，英文 README 与中文 README 保持语义一致。

## 常用命令

- 安装后端依赖：`uv sync`。
- 启动后端：`uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000`。
- 安装前端依赖：在 `frontend/` 中运行 `npm install`。
- 启动前端：在 `frontend/` 中运行 `npm run dev`。
- 构建前端：在 `frontend/` 中运行 `npm run build`。
- 生成接口文档：`uv run python scripts/generate_api_doc.py`。
- 当前仓库没有配置自动化测试、lint 或 formatter；不要声称运行过不存在的检查，也不要仅为完成普通任务擅自引入相关工具。

## 后端约定

- 保持 `router/`、`crud/`、`model/`、`ai/`、`util/` 的职责边界：路由负责鉴权和编排，CRUD 负责数据库访问，Pydantic 模型负责数据约束。
- 不在路由中直接编写 SQL。SQL 必须参数化，并通过 `util/db_util.py` 中的 `get_cursor()` 或 `get_connection()` 管理提交、回滚和关闭。
- 普通业务接口沿用 `model/result.py` 的 `{code, msg, data}` 响应结构：成功 `code=1`，失败 `code=0`。认证、权限和框架校验错误继续使用 FastAPI 标准错误响应。
- 新增或修改接口时必须使用 `require_current_user` 或 `require_admin`，并验证会话、消息、文档、知识库等资源归属。前端路由或按钮可见性不能代替后端权限校验。
- 新增静态子路径时检查其与 `/{id}` 等动态路由的声明顺序，避免被动态路由提前匹配。
- 数据库字段或约束变化时同步检查 `sql/db.sql`、相关 Pydantic 模型、CRUD、路由、前端调用和生成的接口文档。
- `sql/db.sql` 是空环境初始化脚本，不是可重复执行的迁移脚本。已有数据库的结构变化应提供增量 SQL，不要依赖重新初始化数据库。

## AI 与检索约定

- AI 模型、服务地址、密钥读取和检索参数位于 `config/ai_config.py`；提示词正文位于 `config/prompts/`，不得重新内嵌到 Python 文件。
- 提示词文件使用 UTF-8。修改时保留 `{conversation}`、`{user_input}`、`{conversation_history}`、`{user_question}` 等运行时占位符；普通花括号需要按 Python `str.format()` 规则转义。
- `POST /api/message/chat` 必须保持 `application/x-ndjson` 流式协议，逐行发送 `start`、`delta`、`done` 或 `error` 事件，并保持 `frontend/src/api/message.js` 的解析逻辑同步。
- 用户消息在生成前持久化；AI 消息只能在完整生成后持久化。失败、中断或取消的流不得留下不完整的 AI 历史记录。
- ChromaDB 与 Elasticsearch 的切片 ID 必须保持相同的 `document_id_chunk_index` 格式，混合检索依赖该 ID 融合去重。
- 文档上传和删除跨越 OSS、MySQL、ChromaDB 与 Elasticsearch。修改流程时必须明确处理顺序、部分成功、错误返回和补偿策略，不得把单端成功当作整体成功。

## 前后端契约

- 后端接口路径、HTTP 方法、参数名或响应结构变化时，同步更新 `frontend/src/api/` 下的调用方和相关页面。
- 普通前端请求复用 `frontend/src/utils/request.js`；聊天流使用原生 `fetch()`，不要强行改用普通 Axios 响应流程。
- 文件上传类型、大小和文件名限制同时存在于 `config/file_config.py` 与 `frontend/src/utils/uploadValidation.js`，修改任一侧时必须同步另一侧。
- Vite 本地开发通过 `/api` 代理到 `http://127.0.0.1:8000`。不要在业务组件中硬编码后端绝对地址。
- 保持现有 Vue Composition API、`@` 路径别名和 Element Plus 中文本地化用法；共享请求逻辑放在 `frontend/src/api/` 或 `frontend/src/utils/`，不要在多个页面重复实现。

## 文档与生成文件

- 路由、请求模型或公开响应变化后运行 `uv run python scripts/generate_api_doc.py`，提交同步更新的 `接口文档.md`。
- `接口文档.md` 由 `scripts/generate_api_doc.py` 生成，不得手动编辑。
- 用户可见功能、配置、启动步骤或部署要求变化时同步更新 `README.md` 和 `README-en.md`。
- 不提交 `frontend/dist/`、`chroma_db/`、`.venv/`、`__pycache__/`、IDE 配置或其他本地生成内容。

## 安全与破坏性操作

- 不读取、打印、修改或提交根目录 `.env` 中的真实密钥。新增环境变量时只更新 `.env.example`，示例值不得包含真实凭证。
- 不在源码、文档、测试数据或日志中写入 API Key、数据库密码、JWT 密钥、OSS 凭证或访问令牌。
- 未经用户明确授权，禁止执行 `sql/reset-dev.sql`；该脚本会永久删除整个 `xlt` 数据库。
- 未经明确授权，不对真实数据库、检索服务、对象存储、向量数据库或模型服务执行写入、删除、重建索引等验证操作。
- 删除知识库、文档、公告附件或用户数据属于跨系统破坏性操作；实施前确认权限、依赖关系、外部资源清理顺序和失败后的数据状态。

## 验证要求

- 修改 Python 后至少运行针对变更文件的编译检查；涉及多个模块时可运行 `uv run python -m compileall -q ai authentication config crud model router util scripts main.py`。
- 修改前端 JS/Vue 或构建配置后运行 `npm run build`。若环境缺少依赖，明确报告未运行原因。
- 修改提示词后验证四个模板均能以 UTF-8 加载，并验证所有 `.format(...)` 占位符可正常替换。
- 修改路由、鉴权、数据模型或前后端契约时，除静态检查外还应说明尚未覆盖的 MySQL、Elasticsearch、OSS 或模型 API 集成风险。
- 提交前运行 `git diff --check`，并检查 `git status --short`，避免夹带无关文件。

## Git 约定

- 保留用户已有的工作区修改，不回退、不覆盖与任务无关的变更。
- 只有用户明确要求时才创建提交；提交信息使用中文，并按单一职责拆分为便于审阅和回退的小粒度提交。
- 未经用户明确要求绝不推送，不重写已有提交历史，不使用破坏性 Git 命令。

## Code Review Rules

- 优先检查越权访问、资源归属遗漏、敏感信息泄露和破坏性数据库操作。
- 检查 OSS、MySQL、ChromaDB、Elasticsearch 多端写入或删除是否会产生不可恢复的部分状态。
- 检查聊天 NDJSON 事件顺序、错误处理和消息持久化时机是否发生回归。
- 检查后端接口、前端调用、上传限制、提示词占位符、数据库结构和生成文档是否保持同步。
