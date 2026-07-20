import request from "@/utils/request.js";

// 创建角色
export const createRole = (role) => request.post("/role", role);

// 分页查询所有角色
export const getAllRoles = (page, pageSize) => request.get(`/role/all?page=${page}&page_size=${pageSize}`);

// 根据角色名查询角色
export const getRoleByName = (roleName) => request.get(`/role/name/${roleName}`);

// 根据角色ID查询角色
export const getRoleById = (roleId) => request.get(`/role/id/${roleId}`);

// 更新角色
export const updateRole = (role) => request.put("/role", role);

// 删除角色
export const deleteRole = (id) => request.delete(`/role?id=${id}`);

// 搜索角色
export const searchRole = (content) => request.get(`/role/search/${content}`);
