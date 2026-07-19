<script setup>
import {onMounted, ref} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {InfoFilled, Delete, Plus, RefreshRight} from "@element-plus/icons-vue";
import {getAllRoles} from "@/api/role.js";

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
  // TODO 批量删除角色
}

// 新增角色弹窗
const handleAddRole = () => {
  // TODO 新增角色弹窗
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
      <el-table-column prop="name" label="角色名" width="200" show-overflow-tooltip align="center"/>
      <!-- 操作列 -->
      <el-table-column label="操作" width="400" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="" class="action-buttons">
            <el-icon><InfoFilled /></el-icon> 角色详情
          </el-button>

          <el-button type="info" size="small" @click="" class="action-buttons">
            <el-icon><InfoFilled /></el-icon> 知识库详情
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

.action-buttons {
  margin: 0 10px;
}
</style>