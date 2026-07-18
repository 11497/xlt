<script setup>
import {onMounted, ref} from "vue";
import {deleteSession, pageGetUserSessions} from "@/api/session.js";
import {ElMessage, ElMessageBox} from "element-plus";
import {InfoFilled} from "@element-plus/icons-vue";
import SessionMessageDialog from "@/views/user/SessionMessageDialog.vue";

let sessionList = ref([]);

let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);

// 存储当前选中的行
const selectedRows = ref([]);

const getSessions = async () => {
  const res = await pageGetUserSessions(currentPage.value, pageSize.value);
  if (res.code === 1) {
    sessionList.value = res.data.list;
    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } else {
    ElMessage.error(res.msg);
  }
}

onMounted(async () => {
  await getSessions();
})

const handleSizeChange = async () => {
  await getSessions();
}

const handleCurrentChange = async () => {
  await getSessions();
}

// 选中行变化时的回调
const handleSelectionChange = (rows) => {
  selectedRows.value = rows;
}

// 修改后的批量删除方法
const handleDelete = async () => {
  try {
    // 弹出确认框
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 条会话吗？删除后不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    // 用户点击确认后执行删除
    const results = await Promise.allSettled(
      selectedRows.value.map(row => deleteSession(row.id))
    );

    const successCount = results.filter(r => r.status === 'fulfilled' && r.value.code === 1).length;

    if (successCount > 0) {
      ElMessage.success(`成功删除 ${successCount} 条会话`);
    } else {
      ElMessage.error('删除失败');
    }
  } catch (e) {
    // 用户点击取消时，ElMessageBox 会 reject，这里判断是否为取消操作
    if (e === 'cancel' || e?.action === 'cancel') {
      // 用户主动取消，不做任何提示
      return;
    }
    ElMessage.error('删除请求异常');
  } finally {
    await getSessions();
    selectedRows.value = []; // 清空选中状态
  }
}

const dialogVisible = ref(false);
const currentSessionId = ref(null);
const currentSessionName = ref("");

// showMessage 方法
const showMessage = (row) => {
  currentSessionId.value = row.id;
  currentSessionName.value = row.name;
  dialogVisible.value = true;
};
</script>

<template>
  <!-- 操作按钮区域 -->
  <div class="container action-bar">
    <el-button type="danger" :disabled="selectedRows.length === 0" @click="handleDelete">
      删除
    </el-button>
  </div>

  <!-- 表格部分 -->
  <div class="container">
    <el-table :data="sessionList" border style="width: 100%" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center"/>
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column prop="name" label="会话名称" min-width="200" show-overflow-tooltip align="center"/>
      <el-table-column prop="create_time" label="创建时间" width="180" align="center"/>
      <el-table-column prop="update_time" label="修改时间" width="180" align="center"/>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="showMessage(scope.row)">
            <el-icon><InfoFilled /></el-icon> 会话详情
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

  <!-- 会话详情弹窗 -->
  <SessionMessageDialog
    v-model:visible="dialogVisible"
    :session-id="currentSessionId"
    :session-name="currentSessionName"
  />
</template>

<style scoped>
.container {
  margin: 15px 0;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
}
</style>