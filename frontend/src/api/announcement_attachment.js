import request from "@/utils/request.js";
import {ElMessage} from "element-plus";

// 上传公告附件
export const uploadAnnouncementAttachment = (formData) =>
  request.post("/announcement_attachment/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

// 下载公告附件（获取预签名URL后自动下载）
export const downloadAnnouncementAttachment = async (id) => {
  try {
    const res = await request.get(`/announcement_attachment/download/${id}`);
    // 假设 request 的响应拦截器返回的是完整 Result 对象
    if (res.code === 1) {
      const { download_url, filename } = res.data;
      // 创建隐藏的 <a> 标签，模拟点击下载
      const link = document.createElement('a');
      link.href = download_url;
      link.download = filename || 'attachment'; // 指定下载文件名
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

// 删除公告附件
export const deleteAnnouncementAttachment = (id) =>
  request.delete(`/announcement_attachment/${id}`);

// 获取公告的所有附件列表
export const getAnnouncementAttachments = (announcementId) =>
  request.get(`/announcement_attachment/announcement/${announcementId}`);
