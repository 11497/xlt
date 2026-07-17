import request from "@/utils/request.js";

// 分页查询当前用户所有可访问的知识库ID
export const getKnowledgeBases = (page, pageSize) =>
    request.get(`/user_knowledge_base/knowledge_bases?page=${page}&page_size=${pageSize}`);

// 根据用户ID分页查询其所有可访问的知识库ID（管理员）

export const getKnowledgeBasesByUser = (userId, page, pageSize) =>
    request.get(`/user_knowledge_base/user/${userId}?page=${page}&page_size=${pageSize}`);

// 根据知识库ID分页查询所有可访问该知识库的用户ID（管理员）
export const getUsersByKnowledgeBase = (knowledgeBaseId, page, pageSize) =>
    request.get(`/user_knowledge_base/knowledge_bases/${knowledgeBaseId}?page=${page}&page_size=${pageSize}`);