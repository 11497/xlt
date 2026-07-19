<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { getMyRoles } from "@/api/role_user.js";
import {getRoleById} from "@/api/role.js";

let roleIdList = ref([])
let roleList = ref([]);

const getRoleId = async () => {
  const res = await getMyRoles();
  if (res.code === 1) {
    roleIdList.value = res.data;
  } else {
    ElMessage.error(res.msg);
  }
};

const getRole = async () => {
  await getRoleId();
  for (let roleId of roleIdList.value) {
    const res = await getRoleById(roleId);
    if (res.code === 1) {
      roleList.value.push(res.data);
    } else {
      ElMessage.error(res.msg);
    }
  }
}

onMounted(async () => {
  await getRole();
});
</script>

<template>
  <!-- 固定大小的容器 -->
  <div class="container">
    <!-- height="100%" 使表格撑满容器并启用内部滚动 -->
    <el-table :data="roleList" border style="width: 100%" height="100%">
      <!-- 序号列：type="index" 自动生成从1开始的行号 -->
      <el-table-column type="index" label="序号" width="80" align="center" />

      <!-- 角色名称列 -->
      <el-table-column
        prop="name"
        label="角色名字"
        width="200"
        show-overflow-tooltip
        align="center"
      />
    </el-table>
  </div>
</template>

<style scoped>
body {
  margin: 0;
}

.container {
  /* 设置固定高度，可根据实际页面布局调整 */
  height: 600px;
  width: 100%;
  margin: 15px 0;
}
</style>