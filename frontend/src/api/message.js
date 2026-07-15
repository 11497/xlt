import request from "@/utils/request.js";

export const messageBySessionId = (sessionId) => request.get(`/message/session/${sessionId}`)
