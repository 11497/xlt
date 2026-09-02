import request from "@/utils/request.js";
import {ElMessage} from "element-plus";

// 上传文档（异步索引，返回 status: pending）
export const uploadDocument = (formData) =>
  request.post("/document/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

// 下载文档（获取预签名URL后自动下载）
export const downloadDocument = async (id) => {
  try {
    const res = await request.get(`/document/download/${id}`);
    // 假设 request 的响应拦截器返回的是完整 Result 对象
    if (res.code === 1) {
      const { download_url, filename } = res.data;
      // 创建隐藏的 <a> 标签，模拟点击下载
      const link = document.createElement('a');
      link.href = download_url;
      link.download = filename || 'document'; // 指定下载文件名
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      ElMessage.error(res.msg)
    }
  } catch (error) {
    ElMessage.error('下载失败，请稍后重试')
  }
};

// 删除文档（异步：提交删除任务）
export const deleteDocument = (id) => request.delete(`/document/${id}`);

// 查询文档索引状态（前端轮询用）
export const getDocumentStatus = (id) => request.get(`/document/status/${id}`);

// 重新索引文档（failed 或需重建索引）
export const reindexDocument = (id) => request.post(`/document/reindex/${id}`);

// 按知识库分页查询文档列表
export const getDocumentListByKnowledgeBase = (knowledgeBaseId, page = 1, pageSize = 10) =>
  request.get(`/document/knowledge_base/${knowledgeBaseId}`, {
    params: { page, page_size: pageSize }
  });

// 根据ID获取文档详情
export const getDocumentById = (id) => request.get(`/document/${id}`);
