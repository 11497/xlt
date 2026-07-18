<script setup>
import {onMounted, ref} from "vue";
import {pageGetUserSessions} from "@/api/session.js";
import {ElMessage} from "element-plus";
import {InfoFilled} from "@element-plus/icons-vue";
import SessionMessageDialog from "@/views/user/SessionMessageDialog.vue";

let sessionList = ref([]);

let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);

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
  <!-- 表格部分 -->
  <div class="container">
    <el-table :data="sessionList" border style="width: 100%">
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
</style>