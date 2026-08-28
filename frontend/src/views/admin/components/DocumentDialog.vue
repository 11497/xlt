<script setup>
import { ref, reactive } from 'vue';
import { Delete, Upload } from '@element-plus/icons-vue';
import { getDocumentListByKnowledgeBase, deleteDocument, uploadDocument } from '@/api/document.js';
import { ElMessage, ElMessageBox } from 'element-plus';
import { UPLOAD_ACCEPT, validateUploadFile } from '@/utils/uploadValidation.js';

// 状态定义
const dialogVisible = ref(false);
const loading = ref(false);
const currentKbName = ref('');
const documentList = ref([]);

// 上传组件引用
const uploadRef = ref(null);

// 分页参数
const pagination = reactive({
  page: 1,
  pageSize: 5,
  total: 0,
  knowledgeBaseId: null
});


// 打开弹窗并加载数据
const open = (kbId, kbName = '') => {
  pagination.knowledgeBaseId = kbId;
  pagination.page = 1;
  currentKbName.value = kbName;
  dialogVisible.value = true;
  fetchDocuments();
};

// 获取文档列表
const fetchDocuments = async () => {
  if (!pagination.knowledgeBaseId) return;
  loading.value = true;
  try {
    const res = await getDocumentListByKnowledgeBase(
        pagination.knowledgeBaseId,
        pagination.page,
        pagination.pageSize
    );
    if (res.code === 1) {
      documentList.value = res.data.list || [];
      pagination.total = res.data.total || 0;
    } else {
      ElMessage.error(res.msg || '获取文档列表失败');
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('网络请求异常');
  } finally {
    loading.value = false;
  }
};

// 处理删除文档
const handleDelete = (row) => {
  ElMessageBox.confirm(
      `确定要删除文档「${row.filename}」吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
  ).then(async () => {
    try {
      const res = await deleteDocument(row.id);
      if (res.code === 1) {
        ElMessage.success('删除成功');
        await fetchDocuments();
      } else {
        ElMessage.error(res.msg || '删除失败');
      }
    } catch (error) {
      ElMessage.error(error);
    }
  }).catch(() => {});
};

// 自定义上传请求
const handleUploadRequest = async (options) => {
  const formData = new FormData();
  formData.append('file', options.file);
  formData.append('knowledge_base_id', pagination.knowledgeBaseId);

  try {
    const res = await uploadDocument(formData);
    if (res.code === 1) {
      ElMessage.success('上传成功');
      await fetchDocuments();
    } else {
      ElMessage.error(res.msg || '上传失败');
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('上传失败，网络请求异常');
  }
};

// 上传前的校验
const beforeUpload = (file) => {
  const errorMessage = validateUploadFile(file);
  if (errorMessage) {
    ElMessage.error(errorMessage);
    return false;
  }
  return true;
};

// 暴露 open 方法供父组件调用
defineExpose({ open });
</script>

<template>
  <el-dialog
      v-model="dialogVisible"
      :title="`知识库文档列表 - ${currentKbName}`"
      width="900px"
      destroy-on-close
  >
    <!-- 上传按钮区域 -->
    <div class="upload-bar">
      <el-upload
          ref="uploadRef"
          :http-request="handleUploadRequest"
          :before-upload="beforeUpload"
          :show-file-list="false"
          :accept="UPLOAD_ACCEPT"
      >
        <el-button type="primary">
          <el-icon><Upload /></el-icon> 上传文档
        </el-button>
      </el-upload>
    </div>

    <!-- 数据表格 -->
    <el-table :data="documentList" border style="width: 100%" v-loading="loading" empty-text="暂无文档">
      <!-- 1. 序号 -->
      <el-table-column label="序号" width="80" align="center">
        <template #default="{ $index }">
          {{ (pagination.page - 1) * pagination.pageSize + $index + 1 }}
        </template>
      </el-table-column>

      <!-- 2. 文档名 -->
      <el-table-column prop="filename" label="文档名" min-width="200" show-overflow-tooltip />

      <!-- 3. 创建时间 -->
      <el-table-column prop="create_time" label="创建时间" width="180" align="center">
        <template #default="{ row }">
          {{ row.create_time }}
        </template>
      </el-table-column>

      <!-- 4. 修改时间 -->
      <el-table-column prop="update_time" label="修改时间" width="180" align="center">
        <template #default="{ row }">
          {{ row.update_time }}
        </template>
      </el-table-column>

      <!-- 5. 删除按钮 -->
      <el-table-column label="操作" width="120" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="danger" link @click="handleDelete(row)">
            <el-icon><Delete /></el-icon> 删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页组件 -->
    <div class="pagination-container">
      <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[5, 10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchDocuments"
          @current-change="fetchDocuments"
      />
    </div>
  </el-dialog>
</template>

<style scoped>
.upload-bar {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 15px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
