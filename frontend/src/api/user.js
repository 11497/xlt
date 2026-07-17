import request from "@/utils/request.js";

// 用户登录
export const userLogin = (user) => request.post("/user/login", user);

// 查询当前用户信息
export const userInfo = () => request.get("/user");

// 用户注册
export const userRegister = (user) => request.post("/user/register", user);

// 分页查询所有用户信息（管理员）
export const getAllUsers = (params) => request.get("/user/all", { params });

// 管理员更新用户名
export const updateUsername = (data) => request.put("/user/username", null, { params: data });

// 管理员删除用户
export const deleteUser = (id) => request.delete(`/user/${id}`);


// 用户更新密码
export const updatePassword = (data) => request.post("/user/password", null, { params: data });

// 管理员设置用户权限
export const setAdminStatus = (data) => request.put("/user/admin-status", null, { params: data });