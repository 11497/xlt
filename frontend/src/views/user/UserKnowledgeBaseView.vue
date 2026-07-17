<script setup>
import {onMounted, ref} from "vue";
import {ElMessage} from "element-plus";
import {InfoFilled} from "@element-plus/icons-vue";
import {getKnowledgeBases} from "@/api/user_knowledge_base.js";
import DocumentDialog from "@/views/user/DocumentDialog.vue";
import {getKnowledgeBaseById} from "@/api/knowledge_base.js";

let knowledgeBaseList = ref([]);
let knowledgeBaseIdList = ref([]);

let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);

const docDialogRef = ref(null);

const openDocDialog = (kbId, kbName) => {
  docDialogRef.value?.open(kbId, kbName);
};

const getKnowledgeBase = async () => {
  const res = await getKnowledgeBases(currentPage.value, pageSize.value);
  if (res.code === 1) {
    knowledgeBaseIdList.value = res.data.list;

    for (let kbId of knowledgeBaseIdList.value) {
      const kb = await getKnowledgeBaseById(kbId);
      knowledgeBaseList.value.push(kb.data);
    }

    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } else {
    ElMessage.error(res.msg);
  }
}

onMounted(async () => {
  await getKnowledgeBase();
})

const handleSizeChange = async () => {
  await getKnowledgeBase();
}

const handleCurrentChange = async () => {
  await getKnowledgeBase();
}
</script>

<template>
  <!-- 表格部分 -->
  <div class="container">
    <el-table :data="knowledgeBaseList" border style="width: 100%">
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名字" width="200" show-overflow-tooltip align="center"/>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="openDocDialog(scope.row.id, scope.row.name)">
            <el-icon><InfoFilled /></el-icon> 查看文档
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

  <!-- 文档弹窗 -->
  <DocumentDialog ref="docDialogRef"/>
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