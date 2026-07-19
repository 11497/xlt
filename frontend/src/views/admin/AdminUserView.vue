<script setup>
import {onMounted, ref} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {InfoFilled, Delete, Plus, RefreshRight} from "@element-plus/icons-vue";
import {getAllUsers, userRegister} from "@/api/user.js";

// ==================== 列表相关状态 ====================
let userList = ref([]);
let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);
const selectedRows = ref([]);

// ==================== 弹窗相关状态 ====================
// 控制弹窗显示
const dialogVisible = ref(false);
// 弹窗模式: 'detail' | 'add'
const dialogMode = ref('detail');
// 弹窗表单数据
const dialogForm = ref({
  username: '',
  is_admin: false
});

// ==================== 获取用户列表 ====================
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
const handleBatchDelete = () => {
  if (selectedRows.value.length === 0) return;
  ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 条记录吗？`,
      '批量删除确认',
      {confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'}
  ).then(() => {
    // TODO: 在此处调用批量删除接口，方法留空
    console.log('批量删除，选中行:', selectedRows.value);
  }).catch(() => {
    // 用户取消
  });
}

// 用户详情弹窗
const handleDetail = (row) => {
  dialogMode.value = 'detail';
  dialogForm.value = {
    username: row.username,
    is_admin: Boolean(row.is_admin)
  };
  dialogVisible.value = true;
}

const handleSaveDetail = () => {
  // TODO: 在此处调用保存/更新用户接口，方法留空
  console.log('保存用户详情:', dialogForm.value);
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

const handleAddSubmit = async () => {
  if (!dialogForm.value.username?.trim()) {
    ElMessage.warning('用户名不能为空');
    return;
  }
  try {
    const payload = {
      username: dialogForm.value.username.trim(),
      is_admin: dialogForm.value.is_admin ? 1 : 0,
      password: '123456',
      id: null
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
const handleResetPassword = (row) => {
  ElMessageBox.confirm(
      `确定要重置用户「${row.username}」的密码吗？`,
      '重置密码确认',
      {confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'}
  ).then(() => {
    // TODO: 在此处调用重置密码接口，方法留空
    console.log('重置密码，用户:', row);
  }).catch(() => {
    // 用户取消
  });
}
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