<script setup>
import {onMounted, ref} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {InfoFilled, Delete, Plus, User, Notebook} from "@element-plus/icons-vue";
import {createRole, deleteRole, getAllRoles, updateRole} from "@/api/role.js";
import RoleUserDialog from "@/views/admin/RoleUserDialog.vue";
import RoleKnowledgeBaseDialog from "@/views/admin/RoleKnowledgeBaseDialog.vue";

// 列表相关状态
let userList = ref([]);
let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);
const selectedRows = ref([]);

// 获取用户列表
const getRole = async () => {
  const res = await getAllRoles(currentPage.value, pageSize.value);
  if (res.code === 1) {
    userList.value = res.data.list;
    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } else {
    ElMessage.error(res.msg);
  }
}

onMounted(async () => {
  await getRole();
})

const handleSizeChange = async () => {
  await getRole();
}

const handleCurrentChange = async () => {
  await getRole();
}

// 表格选择变化
const handleSelectionChange = (rows) => {
  selectedRows.value = rows;
}

// 批量删除
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedRows.value.length} 个角色吗？`,
        '提示',
        {confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'}
    );
    const ids = selectedRows.value.map(row => row.id);
    for (const id of ids) {
      const res = await deleteRole(id);
      if (res.code !== 1) {
        ElMessage.error(`删除角色ID ${id} 失败: ${res.msg}`);
        return;
      }
    }
    ElMessage.success('批量删除成功');
    await getRole();
  } catch {
    // 用户取消操作
  }
}

// 新增角色弹窗
const handleAddRole = async () => {
  try {
    const {value} = await ElMessageBox.prompt('请输入角色名称', '新增角色', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '角色名称不能为空'
    });
    const res = await createRole({name: value});
    if (res.code === 1) {
      ElMessage.success('新增角色成功');
      await getRole();
    } else {
      ElMessage.error(res.msg);
    }
  } catch {
    // 用户取消操作
  }
}

// 角色详情弹窗
const roleDetailVisible = ref(false);
const roleDetailForm = ref({id: null, name: ''});
const originalRoleName = ref('');

const handleRoleDetail = (row) => {
  roleDetailForm.value = {id: row.id, name: row.name};
  originalRoleName.value = row.name;
  roleDetailVisible.value = true;
}

const handleRoleDetailSave = async () => {
  if (roleDetailForm.value.name === originalRoleName.value) {
    ElMessage.info('角色名未变更');
    roleDetailVisible.value = false;
    return;
  }

  const res = await updateRole({
    id: roleDetailForm.value.id,
    name: roleDetailForm.value.name
  })

  if (res.code === 1) {
    ElMessage.success('角色名修改成功');
  } else {
    ElMessage.error(res.msg);
  }

  roleDetailVisible.value = false;
  await getRole();
}

// 关联用户弹窗
const roleUserDialogVisible = ref(false);
const currentRoleId = ref(null);
const currentRoleName = ref('');

const handleRelationUser = (row) => {
  currentRoleId.value = row.id;
  currentRoleName.value = row.name;
  roleUserDialogVisible.value = true;
}

// 关联知识库弹窗
const roleKbDialogVisible = ref(false);

const handleRelationKb = (row) => {
  currentRoleId.value = row.id;
  currentRoleName.value = row.name;
  roleKbDialogVisible.value = true;
}
</script>

<template>
  <!-- 操作按钮区 -->
  <div class="container action-bar">
    <el-button type="primary" @click="handleAddRole">
      <el-icon><Plus /></el-icon> 新增角色
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
      <el-table-column prop="name" label="角色名" width="250" show-overflow-tooltip align="center"/>
      <!-- 操作列 -->
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="handleRoleDetail(scope.row)" class="action-buttons">
            <el-icon><InfoFilled /></el-icon> 角色详情
          </el-button>
        </template>
      </el-table-column>
      <!--   关联列   -->
      <el-table-column label="关联用户" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="handleRelationUser(scope.row)" class="action-buttons">
            <el-icon><User /></el-icon> 关联用户
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="关联知识库" width="200" align="center">
        <template #default="scope">
          <!--     TODO 关联知识库页面     -->
          <el-button type="info" size="small" @click="handleRelationKb(scope.row)" class="action-buttons">
            <el-icon><Notebook /></el-icon> 关联知识库
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

  <!-- 角色详情弹窗 -->
  <el-dialog v-model="roleDetailVisible" title="角色详情" width="400px">
    <el-form label-width="80px">
      <el-form-item label="角色名称">
        <el-input v-model="roleDetailForm.name" placeholder="请输入角色名称" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="roleDetailVisible = false">取消</el-button>
      <el-button type="primary" @click="handleRoleDetailSave">保存</el-button>
    </template>
  </el-dialog>

  <!-- 关联用户弹窗 -->
  <RoleUserDialog
      v-model:visible="roleUserDialogVisible"
      :role-id="currentRoleId"
      :role-name="currentRoleName"
  />

  <!-- 关联知识库弹窗 -->
  <RoleKnowledgeBaseDialog
      v-model:visible="roleKbDialogVisible"
      :role-id="currentRoleId"
      :role-name="currentRoleName"
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

.action-buttons {
  margin: 0 10px;
}
</style>