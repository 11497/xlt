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
import {getAllKnowledgeBases} from "@/api/knowledge_base.js";

// 列表相关状态
let knowledgeBaseList = ref([]);
let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);
const selectedRows = ref([]); // 存放表格选中的行

// 获取公告列表
const getKnowledgeBase = async () => {
  const res = await getAllKnowledgeBases(currentPage.value, pageSize.value);
  if (res.code === 1) {
    // 将列表中的 is_top 字段从 int (1/0) 转换为 boolean (true/false)
    knowledgeBaseList.value = res.data.list;
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

// 表格选择变化
const handleSelectionChange = (rows) => {
  selectedRows.value = rows;
}
</script>

<template>
  <!-- 操作按钮区 -->
  <div class="container action-bar">
    <el-button type="primary" @click="">
      <el-icon><Plus /></el-icon> 创建知识库
    </el-button>
    <el-button type="danger" @click="" :disabled="selectedRows.length === 0">
      <el-icon><Delete /></el-icon> 批量删除
    </el-button>
  </div>

  <!-- 表格部分 -->
  <div class="container">
    <el-table :data="knowledgeBaseList" border style="width: 100%" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column prop="name" label="知识库名称" width="250" show-overflow-tooltip align="center"/>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="">
            <el-icon><InfoFilled /></el-icon> 知识库文档
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
</style>