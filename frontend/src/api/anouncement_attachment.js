import request from "@/utils/request.js";

// 上传公告附件
export const uploadAnnouncementAttachment = (formData) =>
  request.post("/announcement-attachment/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

// 根据ID下载公告附件
export const downloadAnnouncementAttachment = (id) =>
  request.get(`/announcement-attachment/download/${id}`, { responseType: "blob" });

// 根据ID删除公告附件
export const deleteAnnouncementAttachment = (id) =>
  request.delete(`/announcement-attachment/${id}`);

// 获取指定公告的所有附件列表
export const getAttachmentsByAnnouncementId = (announcementId) =>
  request.get(`/announcement-attachment/announcement/${announcementId}`);