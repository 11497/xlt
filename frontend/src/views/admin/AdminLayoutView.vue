<script setup>
import {ref, watch} from 'vue';
import {ElMessage, ElMessageBox} from "element-plus";
import {useRouter} from "vue-router";
import {useCurrentUser} from "@/hooks/useCurrentUser.js";
import {ChatLineSquare, ChatSquare, House, Message, Notebook, Service, UserFilled} from "@element-plus/icons-vue";
import AppHeader from '@/components/AppHeader.vue';
import AppSidebar from '@/components/AppSidebar.vue';

const router = useRouter();

const {user} = useCurrentUser();
const navigationOpen = ref(false);
const navigationItems = [
  {path: '/admin/index', label: '管理概览', icon: House},
  {path: '/admin/user', label: '用户管理', icon: UserFilled},
  {path: '/admin/role', label: '角色管理', icon: Service},
  {path: '/admin/knowledgeBase', label: '知识库管理', icon: Notebook},
  {path: '/admin/announcement', label: '公告管理', icon: Message},
  {path: '/admin/session', label: '会话管理', icon: ChatSquare}
];

watch(
    () => user.value?.is_admin,
    async (isAdmin) => {
      if (isAdmin === 0) {
        await router.push('/user');
      }
    },
    {immediate: true}
);

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
</script>

<template>
  <div class="workspace-layout">
    <AppHeader :username="user?.username" section="管理工作台" @menu="navigationOpen = true" @logout="logout">
      <template #actions>
        <button class="app-header-link" type="button" aria-label="进入智能问答" title="智能问答" @click="switchToChat">
          <el-icon><ChatLineSquare /></el-icon><span>智能问答</span>
        </button>
      </template>
    </AppHeader>
    <div class="workspace-body">
      <AppSidebar :items="navigationItems" :open="navigationOpen" @close="navigationOpen = false" />
      <el-main class="workspace-main"><div class="workspace-content"><router-view /></div></el-main>
    </div>
  </div>
</template>
