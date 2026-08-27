<script setup>
import {ref} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
import {useRouter} from "vue-router";
import {useCurrentUser} from "@/hooks/useCurrentUser.js";
import {
  ChatLineSquare,
  ChatSquare,
  HomeFilled, Management,
  Menu, Message,
  Notebook,
  Service,
  SwitchButton
} from "@element-plus/icons-vue";

const router = useRouter();

const {user} = useCurrentUser();
const navigationOpen = ref(false);

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
  <div class="common-layout">
    <el-container>
      <el-header class="header">
        <button class="mobile-menu-button" type="button" aria-label="打开导航菜单" title="导航菜单" @click="navigationOpen = true">
          <el-icon><Menu /></el-icon>
        </button>
        <span class="title">校灵通</span>
        <span class="right_tool">
          <a href="javascript:0" @click="switchToChat" class="chat-btn" v-if="user?.is_admin === 0" aria-label="聊天" title="聊天">
            <el-icon><ChatLineSquare /></el-icon> 聊天
          </a>
          <a href="javascript:0" @click="switchToAdmin" class="chat-btn" v-if="user?.is_admin === 1" aria-label="管理" title="管理">
            <el-icon><Management /></el-icon> 管理
          </a>
          <a href="javascript:0" @click="logout" class="logout-btn" aria-label="退出登录" title="退出登录">
            <el-icon><SwitchButton/></el-icon> 退出登录 【{{ user?.username }}】
          </a>
        </span>
      </el-header>

      <el-container class="layout-body">
        <div class="mobile-navigation-mask" :class="{ 'is-visible': navigationOpen }" @click="navigationOpen = false"></div>
        <!-- 左侧菜单 -->
        <el-aside width="200px" class="aside" :class="{ 'is-mobile-open': navigationOpen }">
          <!-- 左侧菜单栏 -->
          <el-menu router @select="navigationOpen = false">
            <el-menu-item index="my">
              <el-icon><HomeFilled /></el-icon> 我的信息
            </el-menu-item>

            <el-menu-item index="announcement">
              <el-icon><Message /></el-icon> 查看公告
            </el-menu-item>

            <el-menu-item index="role">
              <el-icon><Service /></el-icon> 我的角色
            </el-menu-item>

            <el-menu-item index="knowledgeBase">
              <el-icon><Notebook /></el-icon> 我的知识库
            </el-menu-item>

            <el-menu-item index="session">
              <el-icon><ChatSquare /></el-icon> 我的会话
            </el-menu-item>
          </el-menu>
        </el-aside>

        <el-main>
          <router-view></router-view>
        </el-main>
      </el-container>

    </el-container>
  </div>
</template>

<style scoped>
.header {
  background-image: linear-gradient(to right, #00547d, #007fa4, #00aaa0);
  display: flex;
  align-items: center;
}

.title {
  color: white;
  font-size: 40px;
  font-family: 楷体,serif;
  line-height: 60px;
  font-weight: bolder;
}

.right_tool {
  margin-left: auto;
  line-height: 60px;
}

a {
  text-decoration: none;
}

.logout-btn {
  color: red;
  margin: 0 15px;
  font-size: 18px;
}

.chat-btn {
  color: white;
  margin: 0 15px;
  font-size: 18px;
}

.aside {
  border-right: 1px solid #ccc;
  min-height: calc(100vh - 60px);
}

@media (max-width: 768px) {
  .header { height: 52px; padding: 0 12px; }
  .mobile-menu-button { display: inline-flex; width: 36px; height: 36px; padding: 0; margin-right: 8px; align-items: center; justify-content: center; border: 0; background: transparent; color: #fff; font-size: 22px; }
  .title { font-size: 28px; line-height: 52px; }
  .right_tool { display: flex; align-items: center; line-height: 52px; }
  .chat-btn, .logout-btn { display: inline-flex; width: 36px; height: 36px; margin: 0 2px; align-items: center; justify-content: center; font-size: 0; }
  .chat-btn .el-icon, .logout-btn .el-icon { font-size: 20px; }
  .layout-body { min-height: calc(100dvh - 52px); }
  .aside { position: fixed; z-index: 2002; top: 52px; bottom: 0; left: 0; width: min(82vw, 280px) !important; min-height: 0; background: #fff; transform: translateX(-100%); transition: transform 0.2s ease; box-shadow: 4px 0 16px rgb(0 0 0 / 18%); }
  .aside.is-mobile-open { transform: translateX(0); }
  .mobile-navigation-mask { position: fixed; z-index: 2001; inset: 52px 0 0; display: block; background: rgb(0 0 0 / 40%); opacity: 0; visibility: hidden; transition: opacity 0.2s ease, visibility 0.2s ease; }
  .mobile-navigation-mask.is-visible { opacity: 1; visibility: visible; }
}
</style>
