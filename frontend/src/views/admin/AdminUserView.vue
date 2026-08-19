<script setup>
import {onMounted, ref} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {InfoFilled, Delete, Plus, RefreshRight, Service} from "@element-plus/icons-vue";
import {deleteUser, getAllUsers, resetPassword, setAdminStatus, updateUsername, userRegister} from "@/api/user.js";
import UserRoleDialog from "@/views/admin/components/UserRoleDialog.vue";

// 列表相关状态
let userList = ref([]);
let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);
const selectedRows = ref([]);

// 弹窗相关状态
// 控制弹窗显示
const dialogVisible = ref(false);
// 弹窗模式: 'detail' | 'add'
const dialogMode = ref('detail');
// 弹窗表单数据
const dialogForm = ref({
  id: null,
  username: '',
  is_admin: false
});

// 获取用户列表
const getUser = async () => {
  const res = await getAllUsers(currentPage.value, pageSize.value);
  if (res.code === 1) {
    userList.value = res.data.list.map(item => ({
      ...item,
      is_top: Boolean(item.is_top)
    }));
    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } else {
    ElMessage.error(res.msg);
  }
}

onMounted(async () => {
  await getUser();
})

const handleSizeChange = async () => {
  await getUser();
}

const handleCurrentChange = async () => {
  await getUser();
}

// 表格选择变化
const handleSelectionChange = (rows) => {
  selectedRows.value = rows;
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请至少选择一个用户');
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个用户吗？此操作不可恢复。`,
      '批量删除确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    );

    const ids = selectedRows.value.map(row => row.id);
    let successCount = 0;
    for (let id of ids) {
      const res = await deleteUser(id);

      if (res.code === 1) {
        successCount++;
      } else {
        ElMessage.error(res.msg || '删除失败');
        break;
      }
    }

    if (successCount === ids.length) {
      ElMessage.success('删除成功');
    }

    selectedRows.value = [];
    await getUser();
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e);
      ElMessage.error('删除请求发生异常');
    }
  }
}

// 用于存储打开弹窗时的原始数据快照
const originalForm = ref({
  username: '',
  is_admin: false
});

// 用户详情弹窗
const handleDetail = (row) => {
  dialogMode.value = 'detail';
  dialogForm.value = {
    id: row.id,
    username: row.username,
    is_admin: Boolean(row.is_admin)
  };
  // 保存原始数据快照用于变更检测
  originalForm.value = {
    id: row.id,
    username: row.username,
    is_admin: Boolean(row.is_admin)
  };
  dialogVisible.value = true;
}

// 保存用户详情（分别检测、分别调用）
const handleSaveDetail = async () => {
  const usernameChanged = dialogForm.value.username !== originalForm.value.username;
  const isAdminChanged = dialogForm.value.is_admin !== originalForm.value.is_admin;

  // 两个属性都没有修改，直接关闭窗口
  if (!usernameChanged && !isAdminChanged) {
    dialogVisible.value = false;
    return;
  }

  try {
    // 用户名被修改，单独调用更新用户名方法
    if (usernameChanged) {
      const res = await updateUsername({
        id: dialogForm.value.id,
        username: dialogForm.value.username.trim()
      })

      if (res.code === 1) {
        ElMessage.success('更新用户名成功');
      } else {
        ElMessage.error(res.msg || '更新用户名失败');
      }
    }

    // 管理员权限被修改，单独调用更新管理员权限方法
    if (isAdminChanged) {
      const res = await setAdminStatus({
        id: dialogForm.value.id,
        isAdmin: dialogForm.value.is_admin ? 1 : 0
      })

      if (res.code === 1) {
        ElMessage.success('更新权限成功');
      } else {
        ElMessage.error(res.msg || '更新权限失败');
      }
    }

    // 更新原始快照，避免重复提交
    originalForm.value = { ...dialogForm.value };
    dialogVisible.value = false;
    await getUser();
  } catch (e) {
    console.error(e);
    ElMessage.error('保存请求发生异常');
  }
}

// 新增用户弹窗
const handleAddUser = () => {
  dialogMode.value = 'add';
  dialogForm.value = {
    username: '',
    is_admin: false
  };
  dialogVisible.value = true;
}

// 新增用户提交
const handleAddSubmit = async () => {
  if (!dialogForm.value.username?.trim()) {
    ElMessage.warning('用户名不能为空');
    return;
  }
  try {
    const payload = {
      username: dialogForm.value.username.trim(),
      is_admin: dialogForm.value.is_admin ? 1 : 0,
      password: '123456'
    };
    const res = await userRegister(payload);

    if (res.code === 1) {
      ElMessage.success('新增成功');
      dialogVisible.value = false;
      await getUser();
    } else {
      ElMessage.error(res.msg || '新增失败');
    }
  } catch (e) {
    console.error(e);
    ElMessage.error('新增请求发生异常');
  }
}

// 重置密码
const handleResetPassword =  (row) => {
  ElMessageBox.confirm(
      `确定要重置用户「${row.username}」的密码吗？`,
      '重置密码确认',
      {confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'}
  ).then(async () => {
    const res = await resetPassword(row.id);

    if (res.code === 1) {
      ElMessage.success('重置密码成功');
      await getUser();
    } else {
      ElMessage.error(res.msg || '重置密码失败');
    }
  }).catch(() => {
    // 用户取消
  });
}

// 控制用户角色关联弹窗
const userRoleDialogVisible = ref(false);
const currentUser = ref({ id: null, username: '' });

const handleManageRoles = (row) => {
  currentUser.value = { id: row.id, username: row.username };
  userRoleDialogVisible.value = true;
};
</script>

<template>
  <!-- 操作按钮区 -->
  <div class="container action-bar">
    <el-button type="primary" @click="handleAddUser">
      <el-icon><Plus /></el-icon> 新增用户
    </el-button>
    <el-button type="danger" @click="handleBatchDelete" :disabled="selectedRows.length === 0">
      <el-icon><Delete /></el-icon> 批量删除
    </el-button>
  </div>

  <!-- 表格部分 -->
  <div class="container">
    <el-table :data="userList" border style="width: 100%" @selection-change="handleSelectionChange">
      <!-- 复选框列 -->
      <el-table-column type="selection" width="55" align="center" />
      <!-- 序号列 -->
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" width="200" show-overflow-tooltip align="center"/>
      <el-table-column prop="is_admin" label="是否管理员" width="120" align="center">
        <template #default="scope">{{ scope.row.is_admin ? '是' : '否' }}</template>
      </el-table-column>
      <!-- 重置密码列 -->
      <el-table-column label="重置密码" width="120" align="center">
        <template #default="scope">
          <el-button type="danger" size="small" link @click="handleResetPassword(scope.row)">
            <el-icon><RefreshRight /></el-icon> 重置密码
          </el-button>
        </template>
      </el-table-column>
      <!-- 操作列 -->
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="handleDetail(scope.row)">
            <el-icon><InfoFilled /></el-icon> 详情
          </el-button>
        </template>
      </el-table-column>
      <!-- 关联角色列 -->
      <el-table-column label="关联角色" width="150" align="center" fixed="right">
        <template #default="scope">
          <el-button type="info" size="small" @click="handleManageRoles(scope.row)">
            <el-icon><Service /></el-icon> 管理角色
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

  <!-- 复用弹窗：详情 / 新增 -->
  <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'detail' ? '用户详情' : '新增用户'"
      width="460px"
      destroy-on-close
  >
    <el-form :model="dialogForm" label-width="100px">
      <el-form-item label="用户名">
        <el-input v-model="dialogForm.username" placeholder="请输入用户名" />
      </el-form-item>
      <el-form-item label="是否管理员">
        <el-checkbox v-model="dialogForm.is_admin">管理员</el-checkbox>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <!-- 根据模式显示不同按钮 -->
      <el-button v-if="dialogMode === 'detail'" type="primary" @click="handleSaveDetail">保存</el-button>
      <el-button v-else type="primary" @click="handleAddSubmit">新增</el-button>
    </template>
  </el-dialog>

  <!-- 新增：用户角色关联弹窗 -->
  <UserRoleDialog
    v-model:visible="userRoleDialogVisible"
    :user-id="currentUser.id"
    :username="currentUser.username"
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