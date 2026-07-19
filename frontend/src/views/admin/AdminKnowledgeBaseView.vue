<script setup>
import {onMounted, ref} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {InfoFilled, Delete, Plus, Document} from "@element-plus/icons-vue";
import {createKnowledgeBase, deleteKnowledgeBase, getAllKnowledgeBases} from "@/api/knowledge_base.js";

// 列表相关状态
let knowledgeBaseList = ref([]);
let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);
const selectedRows = ref([]); // 存放表格选中的行

// 创建知识库弹窗相关
const createDialogVisible = ref(false);
const createForm = ref({
  name: ""
});

const openCreateDialog = () => {
  createForm.value.name = "";
  createDialogVisible.value = true;
};

const handleCreate = async () => {
  if (!createForm.value.name.trim()) {
    ElMessage.warning("请输入知识库名称");
    return;
  }
  const res = await createKnowledgeBase({
    name: createForm.value.name,
    id: null
  });

  if (res.code === 1) {
    ElMessage.success('创建成功');
  } else {
    ElMessage.error(res.msg);
  }

  createDialogVisible.value = false;
  await getKnowledgeBase();
};

const handleCreateCancel = () => {
  createDialogVisible.value = false;
};

// ========== 批量删除相关 ==========
const handleBatchDelete = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning("请先选择要删除的知识库");
    return;
  }

  ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个知识库吗？此操作不可恢复。`,
      "批量删除确认",
      {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning",
      }
  ).then(async () => {
    let successCount = 0;

    for (const row of selectedRows.value) {
      const res = await deleteKnowledgeBase(row.id);
      if (res.code === 1) {
        successCount ++;
      } else {
        ElMessage.error(res.msg);
      }
    }

    if (successCount > 0) {
      ElMessage.success(`成功删除${successCount}个知识库`);
    }

    await getKnowledgeBase();
  }).catch(() => {
  });
};

// 获取知识库列表
const getKnowledgeBase = async () => {
  const res = await getAllKnowledgeBases(currentPage.value, pageSize.value);
  if (res.code === 1) {
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
    <el-button type="primary" @click="openCreateDialog">
      <el-icon><Plus /></el-icon> 创建知识库
    </el-button>
    <el-button type="danger" @click="handleBatchDelete" :disabled="selectedRows.length === 0">
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
            <el-icon><InfoFilled /></el-icon> 详情
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="文档" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="">
            <el-icon><Document /></el-icon> 查看文档
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

  <!-- 创建知识库弹窗 -->
  <el-dialog v-model="createDialogVisible" title="创建知识库" width="420" :close-on-click-modal="false">
    <el-form>
      <el-form-item label="知识库名称">
        <el-input v-model="createForm.name" placeholder="请输入知识库名称" clearable />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleCreateCancel">取消</el-button>
      <el-button type="primary" @click="handleCreate">确认</el-button>
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
</style>