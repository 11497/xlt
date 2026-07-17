import request from "@/utils/request.js";

// 创建知识库
export const createKnowledgeBase = (knowledgeBase) => request.post("/knowledge_base", knowledgeBase)

// 分页查询所有知识库
export const getAllKnowledgeBases = (page, pageSize) => request.get(`/knowledge_base/all?page=${page}&page_size=${pageSize}`)

// 更新知识库
export const updateKnowledgeBase = (knowledgeBase) => request.put("/knowledge_base", knowledgeBase)

// 删除知识库
export const deleteKnowledgeBase = (id) => request.delete(`/knowledge_base?id=${id}`)

// 根据ID查询知识库
export const getKnowledgeBaseById = (id) => request.get(`/knowledge_base/${id}`)
