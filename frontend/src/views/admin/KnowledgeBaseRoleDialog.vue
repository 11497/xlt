<script setup>
import { ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Delete, Plus } from "@element-plus/icons-vue";
import {batchAssignRoleToKnowledgeBase, getRolesByKnowledgeBase} from "@/api/role_knowledge_base.js";
import {searchRole} from "@/api/role.js";

const props = defineProps({
  visible: { type: Boolean, default: false },
  knowledgeBaseId: { type: Number, default: null },
  knowledgeBaseName: { type: String, default: '' }
});

const emit = defineEmits(['update:visible']);

// 已关联角色列表状态
const roleList = ref([]);
const currentPage = ref(1);
const pageSize = ref(5);
const total = ref(0);
const background = ref(true);
const selectedRows = ref([]);

// 获取知识库已关联的角色列表
const getKnowledgeBaseRoles = async () => {
  const res = await getRolesByKnowledgeBase(props.knowledgeBaseId, currentPage.value, pageSize.value);
  if (res.code === 1) {
    roleList.value = res.data.list;
    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } else {
    ElMessage.error(res.msg);
  }
};

watch(() => props.visible, (val) => {
  if (val && props.knowledgeBaseId) {
    currentPage.value = 1;
    getKnowledgeBaseRoles();
  }
});

const handleSizeChange = () => getKnowledgeBaseRoles();
const handleCurrentChange = () => getKnowledgeBaseRoles();
const handleSelectionChange = (rows) => { selectedRows.value = rows; };

// 批量取消关联
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要取消选中的 ${selectedRows.value.length} 个角色关联吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    );
    // TODO: 调用批量取消知识库角色关联的API
    // const roleIds = selectedRows.value.map(row => row.id);
    // const res = await batchRemoveRolesFromKnowledgeBase(props.knowledgeBaseId, roleIds);
    // if (res.code === 1) {
    //   ElMessage.success('批量取消关联成功');
    //   await getKnowledgeBaseRoles();
    // } else {
    //   ElMessage.error(res.msg);
    // }
  } catch {
    // 用户取消操作
  }
};

// 增加关联弹窗状态
const addDialogVisible = ref(false);
const searchKeyword = ref('');
const searchResults = ref([]);
const selectedRoles = ref([]);

const handleAddRelation = () => {
  searchKeyword.value = '';
  searchResults.value = [];
  selectedRoles.value = [];
  addDialogVisible.value = true;
};

const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入角色ID或角色名进行搜索');
    return;
  }

  const res = await searchRole(searchKeyword.value);
  if (res.code === 1) {
    searchResults.value = res.data;
  } else {
    ElMessage.error(res.msg);
  }
};

const handleSearchSelectionChange = (rows) => { selectedRoles.value = rows; };

const handleCreateRelation = async () => {
  if (selectedRoles.value.length === 0) {
    ElMessage.warning('请先搜索并选择角色');
    return;
  }

  const roleIds = selectedRoles.value.map(role => role.id);
  let successCount = 0;
  for (const roleId of roleIds) {
    const res = await batchAssignRoleToKnowledgeBase(props.knowledgeBaseId, [roleId]);
    if (res.code === 1) {
      successCount ++;
    } else {
      ElMessage.error(res.msg || `关联角色ID ${roleId} 失败`);
    }
  }

  if (successCount > 0) {
    ElMessage.success(`成功关联 ${successCount} 个角色`);
  }

  addDialogVisible.value = false;
  await getKnowledgeBaseRoles();
};

const handleClose = () => { emit('update:visible', false); };
</script>

<template>
  <!-- 知识库关联角色弹窗 -->
  <el-dialog :model-value="visible" title="知识库关联角色" width="700px" @close="handleClose">
    <div class="action-bar">
      <el-button type="primary" @click="handleAddRelation">
        <el-icon><Plus /></el-icon> 增加关联
      </el-button>
      <el-button type="danger" @click="handleBatchDelete" :disabled="selectedRows.length === 0">
        <el-icon><Delete /></el-icon> 批量取消关联
      </el-button>
    </div>

    <el-table :data="roleList" border style="width: 100%; margin-top: 10px;" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column label="知识库名称" align="center">
        <template #default>{{ props.knowledgeBaseName }}</template>
      </el-table-column>
      <el-table-column prop="name" label="角色名" align="center" />
    </el-table>

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

  <!-- 增加关联角色弹窗 -->
  <el-dialog v-model="addDialogVisible" title="增加关联角色" width="500px">
    <el-form label-width="100px">
      <el-form-item label="知识库信息">
        <div style="display: flex; gap: 16px; width: 100%;">
          <el-input :model-value="knowledgeBaseId" disabled style="width: 40%;" />
          <el-input :model-value="knowledgeBaseName" disabled style="width: 60%;" />
        </div>
      </el-form-item>

      <el-form-item label="搜索角色">
        <div style="display: flex; gap: 8px; width: 100%;">
          <el-input v-model="searchKeyword" placeholder="输入角色ID或角色名搜索" clearable @keyup.enter="handleSearch" />
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </div>
      </el-form-item>
    </el-form>

    <el-table
      :data="searchResults"
      border
      style="width: 100%; margin-top: 10px;"
      @selection-change="handleSearchSelectionChange"
      max-height="250"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column prop="id" label="角色ID" width="100" align="center" />
      <el-table-column prop="name" label="角色名" align="center" />
    </el-table>

    <div v-if="selectedRoles.length > 0" style="margin-top: 10px; color: #67c23a;">
      ✓ 已选择 {{ selectedRoles.length }} 个角色：
      {{ selectedRoles.map(r => r.name).join('、') }}
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