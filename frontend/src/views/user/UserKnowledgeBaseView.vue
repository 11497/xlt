<script setup>
import {onMounted, ref} from "vue";
import {ElMessage} from "element-plus";
import {InfoFilled} from "@element-plus/icons-vue";
import {getKnowledgeBases} from "@/api/user_knowledge_base.js";
import DocumentDialog from "@/views/user/components/DocumentDialog.vue";
import {getKnowledgeBaseById} from "@/api/knowledge_base.js";

let knowledgeBaseList = ref([]);
let knowledgeBaseIdList = ref([]);

let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);

const docDialogRef = ref(null);

const openDocDialog = (kbId, kbName) => {
  docDialogRef.value?.open(kbId, kbName);
};

const getKnowledgeBase = async () => {
  const res = await getKnowledgeBases(currentPage.value, pageSize.value);
  if (res.code === 1) {
    knowledgeBaseIdList.value = res.data.list;

    for (let kbId of knowledgeBaseIdList.value) {
      const kb = await getKnowledgeBaseById(kbId);
      knowledgeBaseList.value.push(kb.data);
    }

    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } else {
    ElMessage.error(res.msg);
  }
}

onMounted(async () => {
  await getKnowledgeBase();
})

const handleSizeChange = async () => {
  await getKnowledgeBase();
}

const handleCurrentChange = async () => {
  await getKnowledgeBase();
}
</script>

<template>
  <!-- 表格部分 -->
  <div class="container">
    <el-table :data="knowledgeBaseList" border style="width: 100%">
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名字" width="200" show-overflow-tooltip align="center"/>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="openDocDialog(scope.row.id, scope.row.name)">
            <el-icon><InfoFilled /></el-icon> 查看文档
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

  <!-- 文档弹窗 -->
  <DocumentDialog ref="docDialogRef"/>
</template>

<style scoped>
.container {
  margin: 15px 0;
}
</style>