<script setup>
import { ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Delete, Plus } from "@element-plus/icons-vue";
import {
  batchAssignRoleToKnowledgeBase,
  batchRemoveRolesFromKnowledgeBase,
  getRolesByKnowledgeBase,
  assignKnowledgeBaseToRole
} from "@/api/role_knowledge_base.js";
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
const permissionUpdating = ref(false);

// 获取知识库已关联的角色列表
const getKnowledgeBaseRoles = async () => {
  const res = await getRolesByKnowledgeBase(props.knowledgeBaseId, currentPage.value, pageSize.value);
  if (res.code === 1) {
    roleList.value = res.data.list.map(row => ({ ...row, editingPermission: row.permission }));
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

    const roleIds = selectedRows.value.map(row => row.id);
    const res = await batchRemoveRolesFromKnowledgeBase(props.knowledgeBaseId, roleIds);
    if (res.code === 1) {
      ElMessage.success('批量取消关联成功');
      await getKnowledgeBaseRoles();
    } else {
      ElMessage.error(res.msg);
    }
  } catch {
    // 用户取消操作
  }
};

// 增加关联弹窗状态
const addDialogVisible = ref(false);
const searchKeyword = ref('');
const searchResults = ref([]);
const selectedRoles = ref([]);
const newPermission = ref(0);
const submitting = ref(false);

const handleAddRelation = () => {
  searchKeyword.value = '';
  searchResults.value = [];
  selectedRoles.value = [];
  newPermission.value = 0;
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

const handlePermissionChange = async (row, value) => {
  if (permissionUpdating.value) return;
  permissionUpdating.value = true;
  try {
    const res = await assignKnowledgeBaseToRole(row.id, props.knowledgeBaseId, value);
    if (res.code === 1) {
      row.permission = value;
      row.editingPermission = value;
      ElMessage.success('权限修改成功');
    } else {
      row.editingPermission = row.permission;
      ElMessage.error(res.msg || '权限修改失败');
    }
  } catch {
    row.editingPermission = row.permission;
    ElMessage.error('权限修改失败，请稍后重试');
  } finally { permissionUpdating.value = false; }
};

const handleCreateRelation = async () => {
  if (selectedRoles.value.length === 0) {
    ElMessage.warning('请先搜索并选择角色');
    return;
  }

  const bindings = selectedRoles.value.map(role => ({ role_id: role.id, permission: newPermission.value }));
  submitting.value = true;
  try {
    const res = await batchAssignRoleToKnowledgeBase(props.knowledgeBaseId, bindings);
    if (res.code !== 1) {
      ElMessage.error(res.msg || '关联角色失败');
      return;
    }
    ElMessage.success(`成功关联 ${bindings.length} 个角色`);
    addDialogVisible.value = false;
    await getKnowledgeBaseRoles();
  } catch {
    ElMessage.error('关联角色失败，请稍后重试');
  } finally {
    submitting.value = false;
  }
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
      <el-button type="danger" plain @click="handleBatchDelete" :disabled="selectedRows.length === 0">
        <el-icon><Delete /></el-icon> 批量取消关联
      </el-button>
    </div>

    <el-table :data="roleList" border style="width: 100%; margin-top: 10px;" empty-text="暂无关联角色" @selection-change="handleSelectionChange">
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
      <el-table-column label="权限" width="130" align="center"><template #default="{ row }">
        <el-select v-model="row.editingPermission" size="small" :disabled="permissionUpdating" @change="value => handlePermissionChange(row, value)">
          <el-option label="只读" :value="0" /><el-option label="读写" :value="1" />
        </el-select>
      </template></el-table-column>
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
      <el-form-item label="关联权限">
        <el-radio-group v-model="newPermission"><el-radio :value="0">只读</el-radio><el-radio :value="1">读写</el-radio></el-radio-group>
      </el-form-item>
    </el-form>

    <el-table
      :data="searchResults"
      border
      empty-text="搜索后选择需要关联的角色"
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
      <el-button type="primary" :loading="submitting" :disabled="submitting" @click="handleCreateRelation">创建关联</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.action-bar {
  display: flex;
  gap: 10px;
}
</style>
