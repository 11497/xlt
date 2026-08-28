<script setup>
import { ref, reactive } from 'vue';
import { Download } from '@element-plus/icons-vue';
import { getDocumentListByKnowledgeBase, downloadDocument } from '@/api/document.js'; // 根据实际路径调整
import { ElMessage } from 'element-plus';

// 状态定义
const dialogVisible = ref(false);
const loading = ref(false);
const currentKbName = ref('');
const documentList = ref([]);

// 分页参数
const pagination = reactive({
  page: 1,
  pageSize: 5,
  total: 0,
  knowledgeBaseId: null
});

/**
 * 打开弹窗并加载数据
 * @param {number} kbId 知识库ID
 * @param {string} kbName 知识库名称(用于标题显示)
 */
const open = (kbId, kbName = '') => {
  pagination.knowledgeBaseId = kbId;
  pagination.page = 1; // 重置到第一页
  currentKbName.value = kbName;
  dialogVisible.value = true;
  fetchDocuments();
};

/**
 * 获取文档列表
 */
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

/**
 * 处理下载
 */
const handleDownload = async (docId) => {
  // 调用 document.js 中已封装好的下载方法
  await downloadDocument(docId);
};

// 暴露 open 方法供父组件调用
defineExpose({ open });
</script>

<template>
  <!-- 文档列表弹窗 -->
  <el-dialog
    v-model="dialogVisible"
    :title="`知识库文档列表 - ${currentKbName}`"
    width="900px"
    destroy-on-close
  >
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

      <!-- 5. 下载按钮 -->
      <el-table-column label="操作" width="120" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleDownload(row.id)">
            <el-icon><Download /></el-icon> 下载
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页组件 (参考知识库分页格式) -->
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
.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
