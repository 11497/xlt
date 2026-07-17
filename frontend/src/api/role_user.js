import request from "@/utils/request.js";

// 批量为角色分配用户
export const batchAssignUsersToRole = (roleId, userIds) =>
  request.post("/role_user/assign", { role_id: roleId, user_ids: userIds });

// 批量从指定角色中移除用户
export const batchRemoveUsersFromRole = (roleId, userIds) =>
  request.delete("/role_user/remove", { data: { role_id: roleId, user_ids: userIds } });

// 按角色分页查询关联的用户
export const getUsersByRole = (roleId, page = 1, pageSize = 10) =>
  request.get(`/role_user/role/${roleId}/users?page=${page}&page_size=${pageSize}`);

// 按用户分页查询关联的角色
export const getRolesByUser = (userId, page = 1, pageSize = 10) =>
  request.get(`/role_user/user/${userId}/roles?page=${page}&page_size=${pageSize}`);

// 获取当前用户的所有角色ID
export const getMyRoles = () => request.get("/role_user/my_roles");

// 分配单个用户到指定角色
export const assignUserToRole = (roleId, userId) =>
  request.post("/role_user/assign_single", { role_id: roleId, user_id: userId });

// 从指定角色中移除单个用户
export const removeUserFromRole = (roleId, userId) =>
  request.delete("/role_user/remove_single", { data: { role_id: roleId, user_id: userId } });

// 删除指定角色的所有用户关联关系
export const deleteByRole = (roleId) =>
  request.delete(`/role_user/by_role/${roleId}`);

// 删除指定用户的所有角色关联关系
export const deleteByUser = (userId) =>
  request.delete(`/role_user/by_user/${userId}`);