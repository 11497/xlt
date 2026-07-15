<script setup>
import {useCurrentUser} from "@/hooks/useCurrentUser.js";
import {ref, watch} from "vue";
import {sessionByUserId} from "@/api/session.js";
import {messageBySessionId} from "@/api/message.js";
import {ElMessage} from "element-plus";

const {user} = useCurrentUser();

let sessions = ref([]);
const sessionsLoading = ref(false);

watch(
    () => user.value?.id,
    async (newId) => {
      if (!newId) return;  // 跳过初始的空值

      sessionsLoading.value = true;
      try {
        const res = await sessionByUserId(newId);
        sessions.value = res.data;
      } finally {
        sessionsLoading.value = false;
      }
    },
    {immediate: true}  // 如果 user 在 watch 注册前已有值，立即执行一次
);

let messages = ref([]);

const handleSessionClick = async (sessionId) => {
  const res = await messageBySessionId(sessionId);
  if (res.code) {
    messages.value = res.data;
    console.log(messages.value);
  } else {
    ElMessage.error(res.msg);
  }
};
</script>

<template>
  <div class="app-layout"> <!-- 替换 common-layout -->
    <header class="app-header">
      <div class="header-left">校灵通</div>
      <div class="header-center">中间</div>
      <div class="header-right">欢迎，{{ user?.username }}</div>
    </header>

    <main class="app-main">
      <aside class="main-left">
        <div class="sessions-header">对话列表</div>
        <el-button type="primary" class="sessions-create-btn">创建对话</el-button>
        <div class="sessions-list">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="session-item"
            @click="handleSessionClick(session.id)"
          >
            <div class="session-name">{{ session.name }}</div>
          </div>
          <div v-if="sessionsLoading" class="loading-text">加载中...</div>
          <div v-else-if="sessions && sessions.length === 0" class="empty-text">暂无会话</div>
        </div>
      </aside>

      <section class="main-chat">聊天</section>
    </main>

    <footer class="app-footer">Copyright © 2026-2026 · 校灵通</footer>
  </div>
</template>

<style>
body {
  margin: 0;
}

.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* ⚠️ 必须保留 */
}

/* 2. Header：固定高度，横向排列 */
.app-header {
  height: 60px; /* 根据实际需求调整 */
  flex-shrink: 0; /* 防止被压缩 */
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 20px;
  background-color: #f5f7fa; /* 可选：添加背景色区分 */
}

.header-left {
  font-size: 20px;
  font-weight: bold;
  white-space: nowrap;
}

.header-center {
  flex: 1;
  text-align: center;
}

.header-right {
  white-space: nowrap;
}

/* 3. Main：占据除 header 和 footer 之外的所有剩余空间 */
.el-main {
  flex: 1;
  padding: 0; /* 去除 el-main 默认的 20px padding，避免产生滚动条 */
  overflow: hidden; /* 防止内容溢出导致外层出现滚动条 */
  min-height: 0; /* 关键：允许flex容器收缩 */
}

/* 4. Main 内部容器：横向排列，占满父级高度 */
.app-main {
  flex: 1; /* 关键：替换 height: 100% */
  display: flex;
  overflow: hidden;
}

/* 5. 左侧边栏：固定 200px 宽度 */
.main-left {
  width: 200px;
  flex-shrink: 0;
  background-color: #ffffff;
  border-right: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
  min-height: 0; /* ✅ 保留 */
  /* 删除 height: 100%; */
}

/* 会话列表头部 */
.sessions-header {
  padding: 16px;
  font-weight: bold;
  border-bottom: 1px solid #dcdfe6;
  background-color: #f5f7fa;
  flex-shrink: 0;
}

.sessions-create-btn {
  margin: 15px 15px 5px 6px;
}

/* 会话列表容器 - 需要固定高度和滚动条 */
.sessions-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}

/* 自定义滚动条样式 */
.sessions-list::-webkit-scrollbar {
  width: 4px;
}

.sessions-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.sessions-list::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 2px;
}

.sessions-list::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

/* 每个会话项 */
.session-item {
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.session-item:hover {
  background-color: #f5f7fa;
}

.session-item:last-child {
  border-bottom: none;
}

/* 会话名称 */
.session-name {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 加载和空状态文本 */
.loading-text,
.empty-text {
  padding: 16px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

/* 6. 聊天区域：占据剩余宽度，允许内部滚动 */
.main-chat {
  flex: 1;
  overflow-y: auto; /* 聊天记录过多时，仅聊天区域内部滚动 */
  padding: 16px; /* 聊天内容的内边距 */
  min-height: 0; /* 关键：解决flex容器内的滚动问题 */
}

/* 7. Footer：固定在底部，固定高度 */
.app-footer {
  height: 40px; /* 根据实际需求调整 */
  flex-shrink: 0; /* 防止被压缩 */
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  border-top: 1px solid #dcdfe6;
}
</style>