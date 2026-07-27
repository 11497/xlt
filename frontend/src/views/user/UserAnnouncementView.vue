<script setup>
import {onMounted, ref} from "vue";
import {getAllAnnouncements} from "@/api/announcement.js";
import {getAnnouncementAttachments, downloadAnnouncementAttachment} from "@/api/announcement_attachment.js";
import {ElMessage} from "element-plus";
import {InfoFilled, Download} from "@element-plus/icons-vue";

let announcementList = ref([]);

let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);

// 详情弹窗相关状态
const detailDialogVisible = ref(false);
const currentAnnouncement = ref(null);
const attachmentList = ref([]);
const attachmentLoading = ref(false);

const getAnnouncement = async () => {
  const res = await getAllAnnouncements(currentPage.value, pageSize.value);
  if (res.code === 1) {
    announcementList.value = res.data.list;
    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } else {
    ElMessage.error(res.msg);
  }
}

// 显示详情并加载附件
const showDetail = async (row) => {
  currentAnnouncement.value = row;
  detailDialogVisible.value = true;
  attachmentList.value = []; // 重置附件列表

  attachmentLoading.value = true;
  try {
    const res = await getAnnouncementAttachments(row.id);
    if (res.code === 1) {
      attachmentList.value = res.data || [];
    } else {
      ElMessage.error(res.msg || '获取附件失败');
    }
  } catch (e) {
    console.error(e);
  } finally {
    attachmentLoading.value = false;
  }
}

// 下载附件
const handleDownload = async (attachmentId) => {
  await downloadAnnouncementAttachment(attachmentId);
}

onMounted(async () => {
  await getAnnouncement();
})

const handleSizeChange = async () => {
  await getAnnouncement();
}

const handleCurrentChange = async () => {
  await getAnnouncement();
}
</script>

<template>
  <!-- 表格部分 -->
  <div class="container">
    <el-table :data="announcementList" border style="width: 100%">
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip align="center"/>
      <el-table-column prop="is_top" label="是否置顶" width="120" align="center">
        <template #default="scope">{{ scope.row.is_top ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column prop="create_time" label="发布时间" width="180" align="center"/>
      <el-table-column prop="update_time" label="修改时间" width="180" align="center"/>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="showDetail(scope.row)">
            <el-icon><InfoFilled /></el-icon> 详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>

  <!-- 分页部分 -->
  <div class="container">
    <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[5, 10, 20, 30, 50, 75, 100]"
        :background="background"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
    />
  </div>

  <!-- 公告详情弹窗 -->
  <el-dialog
      v-model="detailDialogVisible"
      :title="currentAnnouncement?.title"
      width="60%"
      top="5vh"
      destroy-on-close
      align-center
  >
    <!-- 弹窗头部样式 -->
    <template #header>
      <div style="text-align: center; font-size: 18px; font-weight: bold;">
        {{ currentAnnouncement?.title }}
      </div>
    </template>

    <!-- 中间可滚动内容区域 -->
    <div class="dialog-content-scroll">
      <!-- 假设公告内容有 content 字段，若无请替换为实际字段名 -->
      <div v-html="currentAnnouncement?.content || '暂无内容'" class="content-body"></div>
    </div>

    <!-- 底部附件区域 -->
    <div class="dialog-footer-attachments">
      <div class="attachment-label">附件列表：</div>
      <div v-loading="attachmentLoading" class="attachment-list">
        <div v-if="attachmentList.length === 0 && !attachmentLoading" class="no-attachment">
          暂无附件
        </div>
        <div
            v-for="item in attachmentList"
            :key="item.id"
            class="attachment-item"
        >
          <el-tooltip :content="item.filename" placement="top">
            <span class="filename-text">{{ item.filename }}</span>
          </el-tooltip>
          <el-button
              type="primary"
              link
              @click="handleDownload(item.id)"
          >
            <el-icon><Download /></el-icon> 下载
          </el-button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<style scoped>
.container {
  margin: 15px 0;
}

/* 中间内容区：可滚动 */
.dialog-content-scroll {
  max-height: 60vh; /* 限制最大高度，超出滚动 */
  overflow-y: auto;
  padding: 10px 0;
  line-height: 1.6;
  color: #333;
}

/* 底部附件区 */
.dialog-footer-attachments {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.attachment-label {
  font-weight: bold;
  margin-bottom: 10px;
  color: #606266;
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.filename-text {
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis; /* 名字太长省略后半部分 */
  margin-right: 15px;
  color: #303133;
}

.no-attachment {
  color: #909399;
  font-style: italic;
  text-align: center;
  padding: 10px;
}
</style>