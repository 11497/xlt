import request from "@/utils/request.js";

export const userLogin = (user) => request.post("/user/login", user);