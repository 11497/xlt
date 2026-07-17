import request from "@/utils/request.js";

// 批量为知识库分配角色
export const batchAssignRoleToKnowledgeBase = (knowledgeBaseId, roleIds) =>
    request.post(`/role_knowledge_base/assign?knowledge_base_id=${knowledgeBaseId}`, roleIds);

// 批量从指定知识库中删除角色
export const batchRemoveRolesFromKnowledgeBase = (knowledgeBaseId, roleIds) =>
    request.delete(`/role_knowledge_base/remove?knowledge_base_id=${knowledgeBaseId}`, { data: roleIds });

// 按角色分页查询关联的知识库
export const getKnowledgeBaseByRole = (roleId, page = 1, pageSize = 10) =>
    request.get(`/role_knowledge_base/role/${roleId}/knowledge_bases?page=${page}&page_size=${pageSize}`);

// 按知识库分页查询关联的角色
export const getRolesByKnowledgeBase = (knowledgeBaseId, page = 1, pageSize = 10) =>
    request.get(`/role_knowledge_base/knowledge_base/${knowledgeBaseId}/roles?page=${page}&page_size=${pageSize}`);

// 为指定角色分配单个知识库
export const assignKnowledgeBaseToRole = (roleId, knowledgeBaseId) =>
    request.post(`/role_knowledge_base/assign_single?role_id=${roleId}&knowledge_base_id=${knowledgeBaseId}`);

// 从指定角色中移除单个知识库
export const removeKnowledgeBaseFromRole = (roleId, knowledgeBaseId) =>
    request.delete(`/role_knowledge_base/remove_single?role_id=${roleId}&knowledge_base_id=${knowledgeBaseId}`);

// 删除指定角色的所有知识库关联关系
export const deleteByRole = (roleId) =>
    request.delete(`/role_knowledge_base/by_role/${roleId}`);

// 删除指定知识库的所有角色关联关系
export const deleteByKnowledgeBase = (knowledgeBaseId) =>
    request.delete(`/role_knowledge_base/by_knowledge_base/${knowledgeBaseId}`);