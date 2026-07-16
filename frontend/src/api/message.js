import request from "@/utils/request.js";

export const messageBySessionId = (sessionId) => request.get(`/message/session/${sessionId}`)

export const chat = (message) => request.post("/message/chat", message)

export const deleteMessagesAfter = (session_id, message_id) => request.delete(`/message/after?session_id=${session_id}&message_id=${message_id}`)