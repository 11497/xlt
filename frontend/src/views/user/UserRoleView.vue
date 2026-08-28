<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { getMyRoles } from "@/api/role_user.js";
import {getRoleById} from "@/api/role.js";
import PageHeader from '@/components/PageHeader.vue';

let roleIdList = ref([])
let roleList = ref([]);
const loading = ref(false);

const getRoleId = async () => {
  const res = await getMyRoles();
  if (res.code === 1) {
    roleIdList.value = res.data;
  } else {
    ElMessage.error(res.msg);
  }
};

const getRole = async () => {
  loading.value = true;
  try {
    await getRoleId();
    roleList.value = [];
    for (let roleId of roleIdList.value) {
      const res = await getRoleById(roleId);
      if (res.code === 1) {
        roleList.value.push(res.data);
      } else {
        ElMessage.error(res.msg);
      }
    }
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await getRole();
});
</script>

<template>
  <PageHeader title="我的角色" description="查看当前账号在校园知识服务中的身份" />
  <div class="container">
    <el-table
      v-loading="loading"
      :data="roleList"
      border
      class="content-width-table"
      style="--table-content-width: 440px"
      empty-text="暂无关联角色"
    >
      <el-table-column type="index" label="序号" width="92" align="center" />
      <el-table-column
        prop="name"
        label="角色名称"
        min-width="260"
        show-overflow-tooltip
        align="center"
      />
    </el-table>
  </div>
</template>
