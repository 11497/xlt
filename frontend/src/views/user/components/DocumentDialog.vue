<script setup>
import { reactive, ref, onBeforeUnmount } from 'vue';
import { Delete, Download, Upload, Refresh } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { deleteDocument, downloadDocument, getDocumentListByKnowledgeBase, uploadDocument, reindexDocument } from '@/api/document.js';
import { UPLOAD_ACCEPT, validateUploadFile } from '@/utils/uploadValidation.js';

const dialogVisible = ref(false);
const loading = ref(false);
const uploadLoading = ref(false);
const currentKbName = ref('');
const permission = ref(0);
const mode = ref('view');
const documentList = ref([]);
const pagination = reactive({ page: 1, pageSize: 5, total: 0, knowledgeBaseId: null });

let pollTimer = null;

const STATUS_META = {
  pending: { text: '待索引', type: 'warning' },
  indexing: { text: '索引中', type: 'warning' },
  ready: { text: '可用', type: 'success' },
  failed: { text: '失败', type: 'danger' },
  deleting: { text: '删除中', type: 'info' },
};
const statusMeta = (status) => STATUS_META[status] || { text: status || '未知', type: 'info' };
const hasActive = () => documentList.value.some((d) => ['pending', 'indexing', 'deleting'].includes(d.status));

const canManage = () => mode.value === 'manage' && permission.value === 1;
const resetState = () => {
  pagination.knowledgeBaseId = null; pagination.page = 1; pagination.total = 0;
  currentKbName.value = ''; permission.value = 0; mode.value = 'view'; documentList.value = [];
  stopPolling();
};
const stopPolling = () => {
  if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; }
};
const startPolling = () => {
  stopPolling();
  pollTimer = setTimeout(async () => {
    if (!dialogVisible.value) { stopPolling(); return; }
    if (hasActive()) {
      await fetchDocuments(true);
      pollTimer = setTimeout(startPolling, 1500);
    } else {
      stopPolling();
    }
  }, 1500);
};

const open = (options, kbName = '', legacyPermission = 0) => {
  const config = typeof options === 'object' ? options : { id: options, name: kbName, permission: legacyPermission };
  resetState();
  pagination.knowledgeBaseId = config.id;
  currentKbName.value = config.name || '';
  permission.value = config.permission === 1 ? 1 : 0;
  mode.value = config.mode === 'manage' ? 'manage' : 'view';
  dialogVisible.value = true;
  fetchDocuments();
  startPolling();
};
const fetchDocuments = async (silent = false) => {
  if (!pagination.knowledgeBaseId) return;
  if (!silent) loading.value = true;
  try {
    const res = await getDocumentListByKnowledgeBase(pagination.knowledgeBaseId, pagination.page, pagination.pageSize);
    if (res.code === 1) { documentList.value = res.data.list || []; pagination.total = res.data.total || 0; }
    else ElMessage.error(res.msg || '获取文档列表失败');
  } catch { ElMessage.error('获取文档列表失败，请稍后重试'); }
  finally {
    loading.value = false;
    if (hasActive()) startPolling(); else stopPolling();
  }
};
const handleDownload = (id) => downloadDocument(id);
const handleDelete = async (row) => {
  if (!canManage()) return;
  if (row.status === 'deleting') { ElMessage.warning('该文档正在删除中'); return; }
  try {
    await ElMessageBox.confirm(`确定要删除文档「${row.filename}」吗？此操作不可恢复。`, '删除确认', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' });
    const res = await deleteDocument(row.id);
    if (res.code !== 1) { ElMessage.error(res.msg || '删除失败'); return; }
    ElMessage.success('删除任务已提交');
    if (documentList.value.length === 1 && pagination.page > 1) pagination.page -= 1;
    await fetchDocuments();
    startPolling();
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error('删除失败，请稍后重试');
  }
};
const handleReindex = async (row) => {
  try {
    const res = await reindexDocument(row.id);
    if (res.code === 1) {
      ElMessage.success('已重新提交索引任务');
      await fetchDocuments();
      startPolling();
    } else {
      ElMessage.error(res.msg || '重新索引失败');
    }
  } catch {
    ElMessage.error('重新索引失败，请稍后重试');
  }
};
const beforeUpload = (file) => {
  if (!canManage()) return false;
  const message = validateUploadFile(file);
  if (message) ElMessage.error(message);
  return !message;
};
const handleUploadRequest = async (options) => {
  if (!canManage() || uploadLoading.value) return;
  uploadLoading.value = true;
  const formData = new FormData();
  formData.append('file', options.file); formData.append('knowledge_base_id', pagination.knowledgeBaseId);
  try {
    const res = await uploadDocument(formData);
    if (res.code === 1) { ElMessage.success('上传成功，正在后台索引'); options.onSuccess?.(res); await fetchDocuments(); startPolling(); }
    else { ElMessage.error(res.msg || '上传失败'); options.onError?.(new Error(res.msg || '上传失败')); }
  } catch { ElMessage.error('上传失败，请稍后重试'); options.onError?.(new Error('上传失败')); }
  finally { uploadLoading.value = false; }
};
onBeforeUnmount(stopPolling);
defineExpose({ open });
</script>

<template>
  <el-dialog v-model="dialogVisible" :title="`知识库文档列表 - ${currentKbName}`" width="900px" destroy-on-close @closed="resetState">
    <div v-if="canManage()" class="upload-bar">
      <el-upload :http-request="handleUploadRequest" :before-upload="beforeUpload" :show-file-list="false" :accept="UPLOAD_ACCEPT" :disabled="uploadLoading">
        <el-button type="primary" :loading="uploadLoading"><el-icon><Upload /></el-icon> 上传文档</el-button>
      </el-upload>
    </div>
    <el-table :data="documentList" border style="width: 100%" v-loading="loading" empty-text="暂无文档">
      <el-table-column label="序号" width="80" align="center"><template #default="{ $index }">{{ (pagination.page - 1) * pagination.pageSize + $index + 1 }}</template></el-table-column>
      <el-table-column prop="filename" label="文档名" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusMeta(row.status).type" size="small">{{ statusMeta(row.status).text }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="160" align="center" />
      <el-table-column label="操作" width="210" align="center" fixed="right"><template #default="{ row }">
        <el-button type="primary" link @click="handleDownload(row.id)"><el-icon><Download /></el-icon> 下载</el-button>
        <el-button v-if="canManage()" type="danger" link :disabled="row.status === 'deleting'" @click="handleDelete(row)"><el-icon><Delete /></el-icon> 删除</el-button>
        <el-button v-if="canManage() && row.status === 'failed'" type="warning" link @click="handleReindex(row)"><el-icon><Refresh /></el-icon> 重试</el-button>
      </template></el-table-column>
    </el-table>
    <div class="pagination-container"><el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :page-sizes="[5, 10, 20, 50, 100]" :total="pagination.total" layout="total, sizes, prev, pager, next, jumper" @size-change="fetchDocuments" @current-change="fetchDocuments" /></div>
  </el-dialog>
</template>

<style scoped>
.upload-bar { display: flex; justify-content: flex-start; margin-bottom: 15px; }
.pagination-container { display: flex; justify-content: flex-end; margin-top: 20px; }
</style>
