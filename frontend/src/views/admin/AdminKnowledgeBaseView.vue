<script setup>
import {nextTick, onMounted, ref} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {InfoFilled, Delete, Plus, Document, Service} from "@element-plus/icons-vue";
import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  getAllKnowledgeBases,
  updateKnowledgeBase
} from "@/api/knowledge_base.js";
import DocumentDialog from "@/views/admin/components/DocumentDialog.vue";
import KnowledgeBaseRoleDialog from "@/views/admin/components/KnowledgeBaseRoleDialog.vue";
import PageHeader from '@/components/PageHeader.vue';

// 列表相关状态
let knowledgeBaseList = ref([]);
let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);
const selectedRows = ref([]); // 存放表格选中的行

// 创建知识库弹窗相关
const createDialogVisible = ref(false);
const createFormRef = ref(null);
const detailFormRef = ref(null);
const createForm = ref({
  name: ""
});

const nameRules = {
  name: [{
    validator: (_rule, value, callback) => {
      const name = value?.trim() || '';
      if (!name) callback(new Error('请输入知识库名称'));
      else if (Array.from(name).length > 15) callback(new Error('知识库名称不能超过 15 个字符'));
      else callback();
    },
    trigger: 'blur'
  }]
};

const openCreateDialog = () => {
  createForm.value.name = "";
  createDialogVisible.value = true;
  nextTick(() => createFormRef.value?.clearValidate());
};

const handleCreate = async () => {
  const valid = await createFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  const name = createForm.value.name.trim();
  const res = await createKnowledgeBase({
    name
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

// 批量删除相关
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

// 详情弹窗相关
const detailDialogVisible = ref(false);
const detailForm = ref({
  id: "",
  name: "",
  originalName: "" // 用于对比名称是否更改
});

const openDetailDialog = (row) => {
  detailForm.value.id = row.id;
  detailForm.value.name = row.name;
  detailForm.value.originalName = row.name;
  detailDialogVisible.value = true;
  nextTick(() => detailFormRef.value?.clearValidate());
};

const handleDetailSave = async () => {
  const valid = await detailFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  const newName = detailForm.value.name.trim();
  if (newName === detailForm.value.originalName) {
    ElMessage.info("名称未修改，无需保存");
    detailDialogVisible.value = false;
    return;
  }

  const res = await updateKnowledgeBase({
    id: detailForm.value.id,
    name: newName
  });

  if (res.code === 1) {
    ElMessage.success("修改成功");
  } else {
    ElMessage.error(res.msg);
  }

  detailDialogVisible.value = false;
  await getKnowledgeBase();
};

const handleDetailCancel = () => {
  detailDialogVisible.value = false;
};

const documentDialogRef = ref(null);

const openDocumentDialog = (row) => {
  documentDialogRef.value.open(row.id, row.name);
};

// 新增状态
const kbRoleDialogVisible = ref(false);
const currentKnowledgeBase = ref({ id: null, name: '' });

const handleManageRoles = (row) => {
  currentKnowledgeBase.value = { id: row.id, name: row.name };
  kbRoleDialogVisible.value = true;
};
</script>

<template>
  <PageHeader title="知识库管理" description="维护知识空间、文档内容及角色访问范围" />
  <!-- 操作按钮区 -->
  <div class="container action-bar">
    <el-button type="primary" @click="openCreateDialog">
      <el-icon><Plus /></el-icon> 创建知识库
    </el-button>
    <el-button type="danger" plain @click="handleBatchDelete" :disabled="selectedRows.length === 0">
      <el-icon><Delete /></el-icon> 批量删除
    </el-button>
  </div>

  <!-- 表格部分 -->
  <div class="container">
    <el-table
      :data="knowledgeBaseList"
      border
      class="content-width-table"
      style="--table-content-width: 940px"
      empty-text="暂无知识库"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column prop="name" label="知识库名称" width="250" show-overflow-tooltip align="center"/>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="openDetailDialog(scope.row)">
            <el-icon><InfoFilled /></el-icon> 详情
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="文档" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="openDocumentDialog(scope.row)">
            <el-icon><Document /></el-icon> 查看文档
          </el-button>
        </template>
      </el-table-column>
      <!-- 关联角色列 -->
      <el-table-column label="关联角色" width="150" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="handleManageRoles(scope.row)">
            <el-icon><Service /></el-icon> 管理角色
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>

  <!-- 分页部分 -->
  <div class="container content-width-pagination" style="--table-content-width: 940px">
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
    <el-form ref="createFormRef" :model="createForm" :rules="nameRules">
      <el-form-item label="知识库名称" prop="name">
        <el-input v-model="createForm.name" placeholder="请输入知识库名称" maxlength="15" show-word-limit clearable />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleCreateCancel">取消</el-button>
      <el-button type="primary" @click="handleCreate">确认</el-button>
    </template>
  </el-dialog>

  <!-- 知识库详情弹窗 -->
  <el-dialog v-model="detailDialogVisible" title="知识库详情" width="420" :close-on-click-modal="false">
    <el-form ref="detailFormRef" :model="detailForm" :rules="nameRules" label-width="100px">
      <el-form-item label="知识库ID">
        <el-input v-model="detailForm.id" disabled />
      </el-form-item>
      <el-form-item label="知识库名称" prop="name">
        <el-input v-model="detailForm.name" placeholder="请输入知识库名称" maxlength="15" show-word-limit clearable />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleDetailCancel">取消</el-button>
      <el-button type="primary" @click="handleDetailSave">保存</el-button>
    </template>
  </el-dialog>

  <!-- 文档列表弹窗 -->
  <DocumentDialog ref="documentDialogRef" />

  <!-- 关联角色弹窗 -->
  <KnowledgeBaseRoleDialog
    v-model:visible="kbRoleDialogVisible"
    :knowledge-base-id="currentKnowledgeBase.id"
    :knowledge-base-name="currentKnowledgeBase.name"
  />
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
