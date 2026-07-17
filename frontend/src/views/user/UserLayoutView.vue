<script setup>
import {ref} from 'vue';
import {ElMessage, ElMessageBox} from "element-plus";
import {useRouter} from "vue-router";
import {useCurrentUser} from "@/hooks/useCurrentUser.js";
import {
  ChatLineSquare,
  ChatSquare,
  HomeFilled, Management,
  Message,
  Notebook,
  Service,
  SwitchButton
} from "@element-plus/icons-vue";

const router = useRouter();

const {user} = useCurrentUser();

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
        <span class="title">校灵通</span>
        <span class="right_tool">
          <a href="javascript:0" @click="switchToChat" class="chat-btn" v-if="user?.is_admin === 0">
            <el-icon><ChatLineSquare /></el-icon> 聊天
          </a>
          <a href="javascript:0" @click="switchToAdmin" class="chat-btn" v-if="user?.is_admin === 1">
            <el-icon><Management /></el-icon> 管理
          </a>
          <a href="javascript:0" @click="logout" class="logout-btn">
            <el-icon><SwitchButton/></el-icon> 退出登录 【{{ user?.username }}】
          </a>
        </span>
      </el-header>

      <el-container>
        <!-- 左侧菜单 -->
        <el-aside width="200px" class="aside">
          <!-- 左侧菜单栏 -->
          <el-menu router>
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
}

.title {
  color: white;
  font-size: 40px;
  font-family: 楷体;
  line-height: 60px;
  font-weight: bolder;
}

.right_tool {
  float: right;
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
  width: 220px;
  border-right: 1px solid #ccc;
  height: 730px;
}
</style>
