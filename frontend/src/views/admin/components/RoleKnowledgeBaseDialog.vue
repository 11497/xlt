<script setup>
import {ref, watch} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {Delete, Plus} from "@element-plus/icons-vue";
import {
  assignKnowledgeBaseToRole,
  getKnowledgeBaseByRole, removeKnowledgeBaseFromRole
} from "@/api/role_knowledge_base.js";
import {searchKnowledgeBases} from "@/api/knowledge_base.js";

const props = defineProps({
  visible: {type: Boolean, default: false},
  roleId: {type: Number, default: null},
  roleName: {type: String, default: ''}
});

const emit = defineEmits(['update:visible']);

// 关联知识库列表
const knowledgeBaseList = ref([]);
const currentPage = ref(1);
const pageSize = ref(5);
const total = ref(0);
const background = ref(true);
const selectedRows = ref([]);

// 获取关联知识库列表
const getRoleKnowledgeBase = async () => {
  const res = await getKnowledgeBaseByRole(props.roleId, currentPage.value, pageSize.value);

  if (res.code === 1) {
    knowledgeBaseList.value = res.data.list;
    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } else {
    ElMessage.error(res.msg);
  }
}

watch(() => props.visible, (val) => {
  if (val && props.roleId) {
    currentPage.value = 1;
    getRoleKnowledgeBase();
  }
});

const handleSizeChange = () => getRoleKnowledgeBase();
const handleCurrentChange = () => getRoleKnowledgeBase();

const handleSelectionChange = (rows) => {
  selectedRows.value = rows;
}

// 批量删除关联
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要取消选中的 ${selectedRows.value.length} 个知识库关联吗？`,
      '提示',
      {confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'}
    );
    const knowledgeBaseIds = selectedRows.value.map(row => row.id);

    let successCount = 0
    for (let kbId of knowledgeBaseIds) {
      const res = await removeKnowledgeBaseFromRole(props.roleId, kbId);

      if (res.code === 1) {
        successCount ++;
      } else {
        ElMessage.error(res.msg);
      }
    }

    ElMessage.success(`成功取消${successCount}个知识库关联`)

    await getRoleKnowledgeBase();
  } catch {
    // 用户取消操作
  }
}

// 增加关联弹窗
const addDialogVisible = ref(false);
const searchKeyword = ref('');
const searchResults = ref([]);
const selectedKnowledge = ref([]);

const handleAddRelation = () => {
  searchKeyword.value = '';
  searchResults.value = [];
  selectedKnowledge.value = [];
  addDialogVisible.value = true;
}

const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入知识库ID或知识库名进行搜索');
    return;
  }

  const res = await searchKnowledgeBases(searchKeyword.value);
  if (res.code === 1) {
    searchResults.value = res.data;
  } else {
    ElMessage.error(res.msg);
  }
  console.log(searchResults.value)
}

const handleSearchSelectionChange = (rows) => {
  selectedKnowledge.value = rows;
}

const handleCreateRelation = async () => {
  if (selectedKnowledge.value.length === 0) {
    ElMessage.warning('请先搜索并选择知识库');
    return;
  }
  const knowledgeBaseIds = selectedKnowledge.value.map(item => item.id);

  let allSuccess = true;
  for (const knowledgeId of knowledgeBaseIds) {
    const res = await assignKnowledgeBaseToRole(props.roleId, knowledgeId);

    if (res.code !== 1) {
      ElMessage.error(`关联知识库ID ${knowledgeId} 失败: ${res.msg}`);
      allSuccess = false;
    }
  }

  if (allSuccess) {
    ElMessage.success('全部关联成功');
  }
  addDialogVisible.value = false;
  await getRoleKnowledgeBase();
}

const handleClose = () => {
  emit('update:visible', false);
}
</script>

<template>
  <!-- 关联知识库弹窗 -->
  <el-dialog :model-value="visible" title="关联知识库" width="700px" @close="handleClose">
    <!-- 操作按钮 -->
    <div class="action-bar">
      <el-button type="primary" @click="handleAddRelation">
        <el-icon><Plus /></el-icon> 增加关联
      </el-button>
      <el-button type="danger" @click="handleBatchDelete" :disabled="selectedRows.length === 0">
        <el-icon><Delete /></el-icon> 批量删除关联
      </el-button>
    </div>

    <!-- 表格 -->
    <el-table :data="knowledgeBaseList" border style="width: 100%; margin-top: 10px;" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column label="角色名" align="center">
        <template #default>
          {{ props.roleName }}
        </template>
      </el-table-column>
      <el-table-column prop="name" label="知识库名" align="center" />
    </el-table>

    <!-- 分页 -->
    <div style="margin-top: 15px;">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[5, 10, 20, 30, 50]"
        :background="background"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </el-dialog>

  <!-- 增加关联弹窗 -->
  <el-dialog v-model="addDialogVisible" title="增加关联知识库" width="500px">
    <!-- 角色信息（不可修改） -->
    <el-form label-width="80px">
      <el-form-item label="角色信息">
        <div style="display: flex; gap: 16px; width: 100%;">
          <el-input :model-value="roleId" disabled style="width: 40%;" />
          <el-input :model-value="roleName" disabled style="width: 60%;" />
        </div>
      </el-form-item>

      <!-- 搜索框 -->
      <el-form-item label="搜索">
        <div style="display: flex; gap: 8px; width: 100%;">
          <el-input v-model="searchKeyword" placeholder="输入知识库ID或知识库名搜索" clearable @keyup.enter="handleSearch" />
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </div>
      </el-form-item>
    </el-form>

    <!-- 搜索结果列表 -->
    <el-table
      :data="searchResults"
      border
      style="width: 100%; margin-top: 10px;"
      @selection-change="handleSearchSelectionChange"
      max-height="250"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column prop="id" label="知识库ID" width="100" align="center" />
      <el-table-column prop="name" label="知识库名" align="center" />
    </el-table>

    <!-- 已选知识库提示 -->
    <div v-if="selectedKnowledge.length > 0" style="margin-top: 10px; color: #67c23a;">
      ✓ 已选择 {{ selectedKnowledge.length }} 个知识库：
      {{ selectedKnowledge.map(k => k.name).join('、') }}
    </div>

    <template #footer>
      <el-button @click="addDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleCreateRelation">创建关联</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.action-bar {
  display: flex;
  gap: 10px;
}
</style>