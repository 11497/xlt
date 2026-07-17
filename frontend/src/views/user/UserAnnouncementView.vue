<script setup>
import {onMounted, ref} from "vue";
import {getAllAnnouncements} from "@/api/announcement.js";
import {ElMessage} from "element-plus";
import {InfoFilled} from "@element-plus/icons-vue";

let announcementList = ref([]);

let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);

const getAnnouncement = async () => {
  const res = await getAllAnnouncements(currentPage.value, pageSize.value);
  if (res.code === 1) {
    announcementList.value = res.data.list;
    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } else {
    ElMessage.error(res.msg);
  }
}

onMounted(async () => {
  await getAnnouncement();
})

const handleSizeChange = async () => {
  await getAnnouncement();
}

const handleCurrentChange = async () => {
  await getAnnouncement();
}
</script>

<template>
<!-- 表格 -->
  <div class="container">
    <el-table :data="announcementList" border style="width: 100%" @selection-change="handleSelectionChange">
      <!-- 序号：根据当前页码和每页条数动态计算 -->
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>

      <!-- 标题：过长内容自动省略 -->
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip align="center"/>

      <!-- 是否置顶 -->
      <el-table-column prop="is_top" label="是否置顶" width="120" align="center">
        <template #default="scope">
          {{ scope.row.is_top ? '是' : '否' }}
        </template>
      </el-table-column>

      <!-- 发布时间 -->
      <el-table-column prop="create_time" label="发布时间" width="180" align="center"/>

      <!-- 修改时间 -->
      <el-table-column prop="update_time" label="修改时间" width="180" align="center"/>

      <!-- 详情按钮 -->
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="showDetail(scope.row)">
            <el-icon><InfoFilled /></el-icon>
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>

  <!-- 分页 -->
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
</style>