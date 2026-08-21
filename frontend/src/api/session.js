import request from "@/utils/request.js";

// 查询用户所有会话
export const sessionByUserId = (userId) => request.get(`/session/user?user_id=${userId}`);

// 删除会话
export const deleteSession = (session_id) => request.delete(`/session/${session_id}`)

// 重命名会话
export const renameSession = (session_id, name) => request.put('/session/name', null, {
  params: { session_id, name }
})

// 创建会话
export const createSession = (session) => request.post("/session", session)

// 分页查询所有会话（管理员）
export const getAllSessions = (page = 1, pageSize = 10) => request.get(`/session/all?page=${page}&page_size=${pageSize}`);

// 查询会话详情
export const getSessionById = (sessionId) => request.get(`/session/${sessionId}`);

// 分页查询当前用户的会话
export const pageGetUserSessions = (page = 1, pageSize = 10) => request.get(`/session/user/page?page=${page}&page_size=${pageSize}`);
