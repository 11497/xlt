<script setup>
import {onMounted, ref} from "vue";
import {getAllAnnouncements} from "@/api/announcement.js";
import {ElMessage} from "element-plus";

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
  <!-- TODO: 表格 -->
  <div class="container">
    <el-table :data="announcementList" border style="width: 100%" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center"/>
      <el-table-column prop="name" label="姓名" width="120" align="center"/>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="primary" size="small" @click="edit(scope.row.id)">
            <el-icon>
              <Check/>
            </el-icon>
            编辑
          </el-button>
          <el-button type="danger" size="small" @click="deleteById(scope.row.id)">
            <el-icon>
              <Delete/>
            </el-icon>
            删除
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

</style>