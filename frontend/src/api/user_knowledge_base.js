import request from "@/utils/request.js";

// 分页查询当前用户可访问的知识库及权限，返回项包含 knowledge_base_id 和 permission
export const getKnowledgeBases = (page, pageSize) =>
    request.get("/user_knowledge_base/knowledge_bases", { params: { page, page_size: pageSize } });

// 根据用户ID分页查询其可访问的知识库及权限（管理员）

export const getKnowledgeBasesByUser = (userId, page, pageSize) =>
    request.get(`/user_knowledge_base/user/${userId}`, { params: { page, page_size: pageSize } });

// 根据知识库ID分页查询所有可访问该知识库的用户及权限（管理员）
export const getUsersByKnowledgeBase = (knowledgeBaseId, page, pageSize) =>
    request.get(`/user_knowledge_base/knowledge_bases/${knowledgeBaseId}`, { params: { page, page_size: pageSize } });
