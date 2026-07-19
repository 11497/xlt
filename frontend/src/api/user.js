import request from "@/utils/request.js";

// 用户登录
export const userLogin = (user) => request.post("/user/login", user);

// 查询当前用户信息
export const userInfo = () => request.get("/user");

// 用户注册
export const userRegister = (user) => request.post("/user/register", user);

// 分页查询所有用户信息（管理员）
export const getAllUsers = (page = 1, pageSize = 10) =>
    request.get("/user/all", { params: { page, page_size: pageSize } });

// 管理员更新用户名
export const updateUsername = (data) => request.put("/user/username", data);

// 管理员删除用户
export const deleteUser = (id) => request.delete(`/user/${id}`);

// 用户更新密码
export const updatePassword = (data) => request.put("/user/password", data);

// 管理员重置用户密码
export const resetPassword = (id) => request.put(`/user/reset_password/${id}`);

// 管理员设置用户权限
export const setAdminStatus = (data) => request.put("/user/admin-status", data);

// 管理员根据用户名或ID查询用户
export const searchUsers = (content) => request.get(`/user/search/${content}`);