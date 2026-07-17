import request from "@/utils/request.js";

// 上传公告附件
export const uploadAnnouncementAttachment = (formData) =>
  request.post("/announcement-attachment/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

// 下载公告附件
export const downloadAnnouncementAttachment = (id) =>
  request.get(`/announcement-attachment/download/${id}`, {
    responseType: "blob",
  });

// 删除公告附件
export const deleteAnnouncementAttachment = (id) =>
  request.delete(`/announcement-attachment/${id}`);

// 获取公告的所有附件列表
export const getAnnouncementAttachments = (announcementId) =>
  request.get(`/announcement-attachment/announcement/${announcementId}`);