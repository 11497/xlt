import request from "@/utils/request.js";

export const sessionByUserId = (userId) => request.get(`/session/user?user_id=${userId}`);

export const deleteSession = (session_id) => request.delete(`/session/${session_id}`)

export const renameSession = (session_id, name) => request.put(`/session/name?session_id=${session_id}&name=${name}`)

export const createSession = (session) => request.post("/session", session)

export const getAllSessions = () => request.get("/session/all")