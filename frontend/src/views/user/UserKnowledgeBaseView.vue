<script setup>
import {onMounted, ref} from "vue";
import {ElMessage} from "element-plus";
import {InfoFilled, Setting} from "@element-plus/icons-vue";
import {getKnowledgeBases} from "@/api/user_knowledge_base.js";
import DocumentDialog from "@/views/user/components/DocumentDialog.vue";
import {getKnowledgeBaseById} from "@/api/knowledge_base.js";
import PageHeader from '@/components/PageHeader.vue';

let knowledgeBaseList = ref([]);
let currentPage = ref(1);
let pageSize = ref(5);
let total = ref(0);
const background = ref(true);
const loading = ref(false);

const docDialogRef = ref(null);

const openDocDialog = (row, mode = 'view') => {
  docDialogRef.value?.open({ id: row.id, name: row.name, permission: row.permission, mode });
};

const getKnowledgeBase = async () => {
  loading.value = true;
  try {
    const res = await getKnowledgeBases(currentPage.value, pageSize.value);
    if (res.code !== 1) {
      ElMessage.error(res.msg || '获取知识库失败');
      return;
    }
    const details = await Promise.all(res.data.list.map(async (item) => {
      try {
        const kb = await getKnowledgeBaseById(item.knowledge_base_id);
        if (kb.code !== 1) throw new Error(kb.msg || '获取知识库详情失败');
        return { ...kb.data, permission: item.permission };
      } catch (error) {
        ElMessage.error(`知识库 ${item.knowledge_base_id} 详情加载失败`);
        return null;
      }
    }));
    knowledgeBaseList.value = details.filter(Boolean);
    total.value = res.data.total;
    currentPage.value = res.data.page;
    pageSize.value = res.data.page_size;
  } catch {
    ElMessage.error('获取知识库失败，请稍后重试');
  } finally {
    loading.value = false;
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
  <PageHeader title="我的知识库" description="浏览当前角色可访问的校园知识内容" />
  <!-- 表格部分 -->
  <div class="container">
    <el-table
      :data="knowledgeBaseList"
      border
      class="content-width-table"
      style="--table-content-width: 760px"
      empty-text="暂无可访问的知识库"
      v-loading="loading"
    >
      <el-table-column label="序号" width="80" align="center">
        <template #default="scope">
          {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名字" min-width="240" show-overflow-tooltip align="center"/>
      <el-table-column label="权限" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="row.permission === 1 ? 'success' : 'info'">
            {{ row.permission === 1 ? '读写' : '只读' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="查看文档" width="150" align="center">
        <template #default="scope">
          <el-button type="info" size="small" @click="openDocDialog(scope.row)">
            <el-icon><InfoFilled /></el-icon> 查看文档
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="文档管理" width="150" align="center">
        <template #default="{ row }">
          <el-tooltip :content="row.permission === 0 ? '当前知识库为只读权限' : '管理文档'">
            <span class="permission-action">
              <el-button type="primary" size="small" :disabled="row.permission !== 1" @click="openDocDialog(row, 'manage')">
                <el-icon><Setting /></el-icon> 管理文档
              </el-button>
            </span>
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>
  </div>

  <!-- 分页部分 -->
  <div class="container content-width-pagination" style="--table-content-width: 760px">
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
.permission-action {
  display: inline-flex;
}
</style>
