<script setup>
import {onMounted, ref} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {InfoFilled, Delete, Plus} from "@element-plus/icons-vue";
import {getAllUsers} from "@/api/user.js";

// 列表相关状态
let userList = ref([]);
let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);
const selectedRows = ref([]); // 存放表格选中的行

// 获取用户列表
const getUser = async () => {
  const res = await getAllUsers(currentPage.value, pageSize.value);
  if (res.code === 1) {
    // 将列表中的 is_top 字段从 int (1/0) 转换为 boolean (true/false)
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
</script>

<template>
  <!-- 操作按钮区 -->
  <div class="container action-bar">
    <el-button type="primary" @click="">
      <el-icon><Plus /></el-icon> 新增用户
    </el-button>
    <el-button type="danger" @click="" :disabled="selectedRows.length === 0">
      <el-icon><Delete /></el-icon> 批量删除
    </el-button>
  </div>

  <!-- 表格部分 -->
  <div class="container">
    <el-table :data="userList" border style="width: 100%" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" width="200" show-overflow-tooltip align="center"/>
      <el-table-column prop="is_admin" label="是否管理员" width="120" align="center">
        <template #default="scope">{{ scope.row.is_admin ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="">
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