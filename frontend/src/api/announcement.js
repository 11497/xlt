import request from "@/utils/request.js";

// 新增公告
export const createAnnouncement = (announcement) => request.post("/announcement", announcement);

// 获取所有公告列表
export const getAllAnnouncements = () => request.get("/announcement/all");

// 根据ID查询单个公告详情
export const getAnnouncementById = (id) => request.get(`/announcement/${id}`);

// 修改公告
export const updateAnnouncement = (announcement) => request.put("/announcement", announcement);

// 批量删除公告
export const deleteAnnouncements = (ids) => request.delete("/announcement", { data: ids });