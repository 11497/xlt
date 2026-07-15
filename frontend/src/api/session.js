import request from "@/utils/request.js";

export const sessionByUserId = (userId) => request.get(`/session/user?user_id=${userId}`);