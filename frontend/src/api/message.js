import request from "@/utils/request.js";

// 通过会话ID查询所有消息
export const messageBySessionId = (sessionId) => request.get(`/message/session/${sessionId}`)

// 发送消息
export const chat = (message) => request.post("/message/chat", message)

// 删除指定消息ID及之后的所有消息
export const deleteMessagesAfter = (session_id, message_id) => request.delete(`/message/after?session_id=${session_id}&message_id=${message_id}`)

// 查询消息详情
export const getMessageById = (messageId) => request.get(`/message/${messageId}`);

// 删除指定会话ID下的所有消息
export const deleteMessagesBySessionId = (sessionId) => request.delete(`/message/session/${sessionId}`);