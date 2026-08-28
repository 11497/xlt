<script setup>
import {ref} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {useRouter} from "vue-router";
import {useCurrentUser} from "@/hooks/useCurrentUser.js";
import {ChatLineSquare, ChatSquare, HomeFilled, Management, Message, Notebook, Service} from "@element-plus/icons-vue";
import AppHeader from '@/components/AppHeader.vue';
import AppSidebar from '@/components/AppSidebar.vue';

const router = useRouter();

const {user} = useCurrentUser();
const navigationOpen = ref(false);
const navigationItems = [
  {path: '/user/my', label: '个人工作台', icon: HomeFilled},
  {path: '/user/announcement', label: '校园公告', icon: Message},
  {path: '/user/role', label: '我的角色', icon: Service},
  {path: '/user/knowledgeBase', label: '我的知识库', icon: Notebook},
  {path: '/user/session', label: '我的会话', icon: ChatSquare}
];

const logout = () => {
  ElMessageBox.confirm('确定要退出登录吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    ElMessage.success('退出成功');
    localStorage.removeItem('loginUser');
    await router.push({path: '/login'});
  }).catch(() => {
    ElMessage.info('已取消退出')
  })
}

const switchToChat = async () => {
  await router.push({path: "/chat"})
}

const switchToAdmin = async () => {
  await router.push({path: "/admin"})
}
</script>

<template>
  <div class="workspace-layout">
    <AppHeader :username="user?.username" section="校园知识工作台" @menu="navigationOpen = true" @logout="logout">
      <template #actions>
        <button v-if="user?.is_admin === 0" class="app-header-link" type="button" aria-label="进入智能问答" title="智能问答" @click="switchToChat">
          <el-icon><ChatLineSquare /></el-icon><span>智能问答</span>
        </button>
        <button v-if="user?.is_admin === 1" class="app-header-link" type="button" aria-label="进入管理端" title="管理端" @click="switchToAdmin">
          <el-icon><Management /></el-icon><span>管理端</span>
        </button>
      </template>
    </AppHeader>
    <div class="workspace-body">
      <AppSidebar :items="navigationItems" :open="navigationOpen" @close="navigationOpen = false" />
      <el-main class="workspace-main"><div class="workspace-content"><router-view /></div></el-main>
    </div>
  </div>
</template>
