<script setup>
import {ref, watch} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {Delete, Plus} from "@element-plus/icons-vue";
import {getUsersByRole} from "@/api/role_user.js";

const props = defineProps({
  visible: {type: Boolean, default: false},
  roleId: {type: Number, default: null},
  roleName: {type: String, default: ''}
});

const emit = defineEmits(['update:visible']);

// 关联用户列表
const userList = ref([]);
const currentPage = ref(1);
const pageSize = ref(5);
const total = ref(0);
const background = ref(true);
const selectedRows = ref([]);

// 获取关联用户列表
const getRoleUsers = async () => {
  // TODO 调用后端接口获取关联用户列表，例如：
  const res = await getUsersByRole(props.roleId, currentPage.value, pageSize.value);
  if (res.code === 1) {
    userList.value = res.data.list;
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
    getRoleUsers();
  }
});

const handleSizeChange = () => getRoleUsers();
const handleCurrentChange = () => getRoleUsers();

const handleSelectionChange = (rows) => {
  selectedRows.value = rows;
}

// 批量删除关联
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
        `确定要取消选中的 ${selectedRows.value.length} 个用户关联吗？`,
        '提示',
        {confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'}
    );
    const userIds = selectedRows.value.map(row => row.id);
    // TODO 调用后端接口批量删除关联，例如：
    // for (const userId of userIds) {
    //   const res = await deleteRoleUserApi(props.roleId, userId);
    //   if (res.code !== 1) {
    //     ElMessage.error(`取消关联用户ID ${userId} 失败: ${res.msg}`);
    //     return;
    //   }
    // }
    ElMessage.success('批量取消关联成功');
    await getRoleUsers();
  } catch {
    // 用户取消操作
  }
}

// 增加关联弹窗
const addDialogVisible = ref(false);
const searchKeyword = ref('');
const searchResults = ref([]);
const selectedUser = ref(null);

const handleAddRelation = () => {
  searchKeyword.value = '';
  searchResults.value = [];
  selectedUser.value = null;
  addDialogVisible.value = true;
}

const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入用户ID或用户名进行搜索');
    return;
  }
  // TODO 调用后端接口搜索用户，例如：
  // const res = await searchUsersApi(searchKeyword.value);
  // if (res.code === 1) {
  //   searchResults.value = res.data;
  // } else {
  //   ElMessage.error(res.msg);
  // }
}

const handleSelectUser = (user) => {
  selectedUser.value = user;
}

const handleCreateRelation = async () => {
  if (!selectedUser.value) {
    ElMessage.warning('请先搜索并选择一个用户');
    return;
  }
  // TODO 调用后端接口创建关联，例如：
  // const res = await createRoleUserApi({role_id: props.roleId, user_id: selectedUser.value.id});
  // if (res.code === 1) {
  //   ElMessage.success('关联成功');
  //   addDialogVisible.value = false;
  //   await getRoleUsers();
  // } else {
  //   ElMessage.error(res.msg);
  // }
  ElMessage.success('关联成功');
  addDialogVisible.value = false;
  await getRoleUsers();
}

const handleClose = () => {
  emit('update:visible', false);
}
</script>

<template>
  <!-- 关联用户弹窗 -->
  <el-dialog :model-value="visible" title="关联用户" width="700px" @close="handleClose">
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
    <el-table :data="userList" border style="width: 100%; margin-top: 10px;" @selection-change="handleSelectionChange">
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
      <el-table-column prop="username" label="用户名" align="center" />
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
  <el-dialog v-model="addDialogVisible" title="增加关联用户" width="500px">
    <!-- 角色信息（不可修改） -->
    <el-form label-width="80px">
      <el-form-item label="角色信息">
        <div style="display: flex; gap: 16px; width: 100%;">
          <el-input :model-value="roleId" disabled style="width: 40%;" />
          <el-input :model-value="roleName" disabled style="width: 60%;" />
        </div>
      </el-form-item>

      <!-- 搜索框 -->
      <el-form-item label="搜索用户">
        <div style="display: flex; gap: 8px; width: 100%;">
          <el-input v-model="searchKeyword" placeholder="输入用户ID或用户名搜索" clearable @keyup.enter="handleSearch" />
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </div>
      </el-form-item>
    </el-form>

    <!-- 搜索结果列表 -->
    <el-table
        :data="searchResults"
        border
        style="width: 100%; margin-top: 10px;"
        highlight-current-row
        @current-change="handleSelectUser"
        max-height="250"
    >
      <el-table-column prop="id" label="用户ID" width="100" align="center" />
      <el-table-column prop="username" label="用户名" align="center" />
    </el-table>

    <!-- 已选用户提示 -->
    <div v-if="selectedUser" style="margin-top: 10px; color: #67c23a;">
      ✓ 已选择用户：{{ selectedUser.username }}（ID: {{ selectedUser.id }}）
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