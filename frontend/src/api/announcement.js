import request from "@/utils/request.js";

// 分页查询所有公告
export const getAllAnnouncements = (page = 1, pageSize = 10) =>
  request.get("/announcement/all", { params: { page, page_size: pageSize } });

// 根据ID查询单个公告详情
export const getAnnouncementById = (id) =>
  request.get(`/announcement/${id}`);

// 新增公告（管理员）
export const createAnnouncement = (announcement) =>
  request.post("/announcement", announcement);

// 修改公告（管理员）
export const updateAnnouncement = (announcement) =>
  request.put("/announcement", announcement);

// 批量删除公告（管理员）
export const deleteAnnouncements = (ids) =>
  request.delete("/announcement", { data: ids });