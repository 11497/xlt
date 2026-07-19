<script setup>
import {onMounted, ref} from "vue";
import {createAnnouncement, deleteAnnouncements, getAllAnnouncements, updateAnnouncement} from "@/api/announcement.js";
import {
  deleteAnnouncementAttachment,
  downloadAnnouncementAttachment,
  getAnnouncementAttachments, uploadAnnouncementAttachment
} from "@/api/anouncement_attachment.js";
import {ElMessage, ElMessageBox} from "element-plus";
import {InfoFilled, Download, Delete, Plus} from "@element-plus/icons-vue";

// 列表相关状态
let announcementList = ref([]);
let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);
const selectedRows = ref([]); // 存放表格选中的行

// 详情/编辑弹窗相关状态
const detailDialogVisible = ref(false);
const currentAnnouncement = ref(null);
const attachmentList = ref([]);
const attachmentLoading = ref(false);

// 发布弹窗相关状态
const publishDialogVisible = ref(false);
const publishForm = ref({
  title: '',
  content: '',
  is_top: false
});

// 获取公告列表
const getAnnouncement = async () => {
  const res = await getAllAnnouncements(currentPage.value, pageSize.value);
  if (res.code === 1) {
    // 将列表中的 is_top 字段从 int (1/0) 转换为 boolean (true/false)
    announcementList.value = res.data.list.map(item => ({
      ...item,
      is_top: Boolean(item.is_top)
    }));
    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } else {
    ElMessage.error(res.msg);
  }
}

// 打开发布弹窗
const openPublishDialog = () => {
  publishForm.value = { title: '', content: '', is_top: false };
  publishDialogVisible.value = true;
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请至少选择一条公告');
    return;
  }
  try {
    await ElMessageBox.confirm('确定要删除选中的公告吗？此操作不可恢复。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });

    // 提取选中行的 id 数组
    const ids = selectedRows.value.map(row => row.id);

    // 调用批量删除 API
    const res = await deleteAnnouncements(ids);

    if (res.code === 1) {
      ElMessage.success('删除成功');
      // 刷新列表数据
      await getAnnouncement();
    } else {
      ElMessage.error(res.msg || '删除失败');
    }
  } catch (e) {
    // 用户点击了取消，或者请求发生异常
    if (e !== 'cancel') {
      console.error(e);
      ElMessage.error('删除请求发生异常');
    }
  }
}

// 删除单个附件
const handleDeleteAttachment = async (attachmentId, filename) => {
  try {
    await ElMessageBox.confirm(`确定要删除附件 "${filename}" 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });

    // 1. 调用删除附件 API
    const res = await deleteAnnouncementAttachment(attachmentId);

    if (res.code === 1) {
      // 2. 从本地列表移除
      attachmentList.value = attachmentList.value.filter(item => item.id !== attachmentId);
      ElMessage.success('附件删除成功');
    } else {
      ElMessage.error(res.msg || '删除失败');
    }
  } catch (e) {
    // 用户取消或请求异常
    if (e !== 'cancel') {
      console.error(e);
      ElMessage.error('删除请求发生异常');
    }
  }
}

// 上传附件
const handleUploadAttachment = async (file) => {
  // 1. 创建 FormData 对象
  const formData = new FormData();
  formData.append('file', file.raw); // file.raw 是原始的 File 对象
  formData.append('announcement_id', currentAnnouncement.value.id); // 获取当前正在编辑的公告ID

  try {
    // 2. 调用上传附件 API
    const res = await uploadAnnouncementAttachment(formData);

    if (res.code === 1) {
      // 3. 上传成功，将新附件添加到列表
      attachmentList.value.push(res.data);
      ElMessage.success('附件上传成功');
    } else {
      ElMessage.error(res.msg || '上传失败');
    }
  } catch (e) {
    console.error(e);
    ElMessage.error('上传请求发生异常');
  }

  return false; // 阻止 el-upload 默认行为
}

// 用于存储公告的原始数据，用于比较
let originalAnnouncement = ref(null);

// 显示详情并加载附件
const showDetail = async (row) => {
  // 使用深拷贝，并转换 is_top 为布尔值，避免引用同一个对象
  const rowData = JSON.parse(JSON.stringify(row));
  rowData.is_top = Boolean(rowData.is_top);

  currentAnnouncement.value = rowData;
  // 保存一份原始数据的副本
  originalAnnouncement.value = JSON.parse(JSON.stringify(rowData));

  detailDialogVisible.value = true;
  attachmentList.value = [];

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

// 保存公告详情
const handleSaveAnnouncement = async () => {
  // 1. 变更检测
  if (!originalAnnouncement.value) return;

  const isChanged =
    currentAnnouncement.value.title !== originalAnnouncement.value.title ||
    currentAnnouncement.value.content !== originalAnnouncement.value.content ||
    currentAnnouncement.value.is_top !== originalAnnouncement.value.is_top;

  if (!isChanged) {
    ElMessage.info('内容未作任何修改');
    return;
  }

  // 2. 构建符合后端模型要求的对象
  const updatedAnnouncement = {
    id: currentAnnouncement.value.id,
    title: currentAnnouncement.value.title,
    content: currentAnnouncement.value.content,
    is_top: currentAnnouncement.value.is_top ? 1 : 0, // 模型中 is_top 是 int 类型
    create_time: currentAnnouncement.value.create_time,
    update_time: new Date(),
  };

  try {
    // 3. 调用更新公告 API
    const res = await updateAnnouncement(updatedAnnouncement);

    if (res.code === 1) {
      ElMessage.success('保存成功');
      // 更新原始数据，以便后续再次比较
      originalAnnouncement.value = JSON.parse(JSON.stringify(currentAnnouncement.value));
      // 刷新列表数据
      await getAnnouncement();
      // 4. 关闭详情弹窗
      detailDialogVisible.value = false;
    } else {
      ElMessage.error(res.msg || '保存失败');
    }
  } catch (e) {
    console.error(e);
    ElMessage.error('保存请求发生异常');
  }
}

// 发布公告
const handlePublishAnnouncement = async () => {
  // 1. 构建符合后端模型要求的对象
  const newAnnouncement = {
    title: publishForm.value.title,
    content: publishForm.value.content,
    is_top: publishForm.value.is_top ? 1 : 0, // 模型中 is_top 是 int 类型
    id: null,
    create_time: new Date(),
    update_time: new Date(),
  };

  try {
    // 2. 调用发布公告 API
    const res = await createAnnouncement(newAnnouncement);

    if (res.code === 1) {
      ElMessage.success('发布成功');
      publishDialogVisible.value = false;
      // 3. 刷新列表数据
      await getAnnouncement();
    } else {
      ElMessage.error(res.msg || '发布失败');
    }
  } catch (e) {
    console.error(e);
    ElMessage.error('发布请求发生异常');
  }
}

// 下载附件（保留原有逻辑）
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

// 表格选择变化
const handleSelectionChange = (rows) => {
  selectedRows.value = rows;
}
</script>

<template>
  <!-- 操作按钮区 -->
  <div class="container action-bar">
    <el-button type="primary" @click="openPublishDialog">
      <el-icon><Plus /></el-icon> 发布公告
    </el-button>
    <el-button type="danger" @click="handleBatchDelete" :disabled="selectedRows.length === 0">
      <el-icon><Delete /></el-icon> 批量删除
    </el-button>
  </div>

  <!-- 表格部分 -->
  <div class="container">
    <el-table :data="announcementList" border style="width: 100%" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
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

  <!-- 公告详情/编辑弹窗 -->
  <el-dialog
      v-model="detailDialogVisible"
      title="编辑公告"
      width="60%"
      top="5vh"
      destroy-on-close
      align-center
  >
    <div class="dialog-content-scroll">
      <!-- 标题与置顶选项 -->
      <div class="form-row">
        <el-input
          v-model="currentAnnouncement.title"
          placeholder="请输入公告标题"
          class="form-title-input"
        />
        <el-checkbox
          v-model="currentAnnouncement.is_top"
          class="form-top-checkbox"
        >
          是否置顶
        </el-checkbox>
      </div>

      <!-- 内容输入框 -->
      <el-input
          v-model="currentAnnouncement.content"
          type="textarea"
          :rows="12"
          placeholder="请输入公告内容"
          class="form-content-input"
      />

      <!-- 附件区域 -->
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
            <div class="attachment-info">
              <el-tooltip :content="item.filename" placement="top">
                <span class="filename-text">{{ item.filename }}</span>
              </el-tooltip>
              <el-button type="primary" link @click="handleDownload(item.id)">
                <el-icon><Download /></el-icon> 下载
              </el-button>
            </div>
            <!-- 右上角叉号删除按钮 -->
            <el-button
              type="danger"
              link
              class="attachment-delete-btn"
              @click="handleDeleteAttachment(item.id, item.filename)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 上传文件区域 -->
        <div class="upload-area">
          <el-upload
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleUploadAttachment"
          >
            <el-button type="primary" plain>
              <el-icon><Plus /></el-icon> 上传附件
            </el-button>
          </el-upload>
        </div>
      </div>
    </div>

    <!-- 底部保存按钮 -->
    <template #footer>
      <el-button @click="detailDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSaveAnnouncement">保存</el-button>
    </template>
  </el-dialog>

  <!-- 发布公告弹窗 -->
  <el-dialog
      v-model="publishDialogVisible"
      title="发布公告"
      width="60%"
      top="5vh"
      destroy-on-close
      align-center
  >
    <div class="dialog-content-scroll">
      <div class="form-row">
        <el-input
          v-model="publishForm.title"
          placeholder="请输入公告标题"
          class="form-title-input"
        />
        <el-checkbox
          v-model="publishForm.is_top"
          class="form-top-checkbox"
        >
          是否置顶
        </el-checkbox>
      </div>

      <el-input
          v-model="publishForm.content"
          type="textarea"
          :rows="12"
          placeholder="请输入公告内容"
          class="form-content-input"
      />
    </div>

    <template #footer>
      <el-button @click="publishDialogVisible = false">取消</el-button>
      <el-button type="success" @click="handlePublishAnnouncement">发布</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.container {
  margin: 15px 0;
}

.action-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 0;
}

/* 表单布局 */
.form-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.form-title-input {
  flex: 1;
}

.form-top-checkbox {
  flex-shrink: 0;
}

.form-content-input {
  margin-bottom: 15px;
}

/* 中间内容区：可滚动 */
.dialog-content-scroll {
  max-height: 60vh;
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
  position: relative;
}

.attachment-info {
  display: flex;
  align-items: center;
  flex: 1;
  overflow: hidden;
}

.filename-text {
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin-right: 15px;
  color: #303133;
}

.attachment-delete-btn {
  flex-shrink: 0;
  font-size: 16px;
}

.upload-area {
  margin-top: 12px;
}

.no-attachment {
  color: #909399;
  font-style: italic;
  text-align: center;
  padding: 10px;
}
</style>