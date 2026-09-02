# API 与聊天协议

## API 模块

| 模块             | 路径                           | 说明                             |
|------------------|--------------------------------|----------------------------------|
| OAuth2 认证      | `/api/auth`                    | Swagger OAuth2 表单登录          |
| 用户             | `/api/user`                    | 注册、登录、用户资料和管理员操作 |
| 角色             | `/api/role`                    | 角色增删改查                     |
| 用户角色         | `/api/role_user`               | 用户与角色关联                   |
| 知识库           | `/api/knowledge_base`          | 知识库管理                       |
| 角色知识库       | `/api/role_knowledge_base`     | 角色与知识库关联                 |
| 用户可访问知识库 | `/api/user_knowledge_base`     | 查询用户访问范围                 |
| 文档             | `/api/document`                | 上传（异步索引）、状态查询、重新索引、下载和删除 |
| 会话             | `/api/session`                 | 创建、查询、改名和删除           |
| 消息             | `/api/message`                 | RAG 问答和消息管理               |
| 公告             | `/api/announcement`            | 发布、查询和置顶                 |
| 公告附件         | `/api/announcement_attachment` | 上传、下载和删除                 |

普通业务接口通常需要：

```http
Authorization: Bearer <access-token>
```

业务响应使用 `{code, msg, data}`，成功时 `code=1`，失败时 `code=0`。认证和参数校验等框架级错误使用 FastAPI 标准错误格式。普通注册、登录和认证接口无需身份认证，管理员操作需要相应权限。

## 聊天流式响应

`POST /api/message/chat` 使用 `application/x-ndjson` 返回流式响应。用户消息在生成前保存；AI 消息在完整生成后保存，或在用户显式停止时保存已生成的非空片段。生成失败、客户端直接取消或断开时不保存不完整的 AI 回复。

请求体示例：

```json
{
  "session_id": 1,
  "role": "user",
  "content": "学校图书馆几点关闭？",
  "create_time": "2026-08-20T16:00:00.000Z"
}
```

响应每行都是独立 JSON 事件：

| 类型      | 字段                            | 说明                                      |
|-----------|---------------------------------|-------------------------------------------|
| `start`   | `user_message_id`, `request_id` | 用户消息已保存；`request_id` 用于停止生成 |
| `delta`   | `content`                       | AI 回复文本片段                           |
| `done`    | `assistant_message_id`          | AI 回复完整生成并保存                     |
| `stopped` | `assistant_message_id`          | 用户停止；无内容时 ID 为 `null`           |
| `error`   | `message`                       | 生成失败，不保存不完整回复                |

示例：

```ndjson
{"type":"start","user_message_id":101,"request_id":"40cb2f0e-b79a-4c89-85e3-c80a17e22a35"}
{"type":"delta","content":"学校图书馆"}
{"type":"delta","content":"通常在晚上 22:00 关闭。"}
{"type":"done","assistant_message_id":102}
```

用户显式停止时，前端调用 `POST /api/message/chat/stop/{request_id}`。切换会话、离开页面或尚未取得 `request_id` 时，前端通过 `AbortController` 取消连接，不保存部分 AI 回复。

## 生成接口文档

```bash
uv run python scripts/generate_api_doc.py
```

脚本从 FastAPI OpenAPI Schema 读取路由并覆盖生成 `docs/接口文档.md`。聊天流的事件字段和处理时序以本文件为准。
