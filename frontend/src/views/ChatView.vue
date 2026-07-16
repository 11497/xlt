<script setup>
import {useCurrentUser} from "@/hooks/useCurrentUser.js";
import {ref, watch, nextTick} from "vue";
import {createSession, deleteSession, renameSession, sessionByUserId} from "@/api/session.js";
import {chat, deleteMessagesAfter, messageBySessionId} from "@/api/message.js";
import {ElMessage, ElMessageBox} from "element-plus";
import MarkdownIt from 'markdown-it';
import router from "@/router/index.js";
import {House, SwitchButton} from "@element-plus/icons-vue";

const md = new MarkdownIt({html: true, linkify: true, typographer: true});

const {user} = useCurrentUser();

let sessions = ref([]);
const sessionsLoading = ref(false);
let currentSessionId = ref(0);

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
    currentSessionId.value = sessionId;
    scrollToBottom();
  } else {
    ElMessage.error(res.msg);
  }
};

const inputContent = ref("");
const textareaRef = ref(null);
const messagesContainer = ref(null);

// 自动调整 textarea 高度（1~5行）
const autoResizeTextarea = () => {
  const el = textareaRef.value;
  if (!el) return;

  el.style.height = "auto"; // 重置高度以正确计算 scrollHeight

  const lineHeight = 24; // 与 CSS 中 line-height 保持一致
  const maxHeight = lineHeight * 5; // 最多5行

  if (el.scrollHeight <= maxHeight) {
    el.style.height = el.scrollHeight + "px";
    el.style.overflowY = "hidden";
  } else {
    el.style.height = maxHeight + "px";
    el.style.overflowY = "auto";
  }
};

// 发送消息
const handleSend = async () => {
  const content = inputContent.value.trim();
  if (!content) return;

  const current_content = content;

  // 本地追加消息
  messages.value.push({content, role: "user"});
  inputContent.value = "";

  // 重置输入框高度
  await nextTick(() => {
    autoResizeTextarea();
    scrollToBottom();
  });

  await chat({
    id: null,
    role: "user",
    content: current_content,
    session_id: currentSessionId.value,
    create_time: new Date().toISOString()
  })

  await handleSessionClick(currentSessionId.value);
  const res = await sessionByUserId(user.value.id);
  sessions.value = res.data;

  scrollToBottom();
};

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    const container = messagesContainer.value;
    if (container) container.scrollTop = container.scrollHeight;
  });
};

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

// 重命名会话
const handleRename = (session) => {
  ElMessageBox.prompt(`确定要重命名会话「${session.name}」吗？`, '重命名', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'info'
  }).then(async ({value}) => {
    await renameSession(session.id, value)
    const res = await sessionByUserId(user.value.id);
    sessions.value = res.data;
  }).catch(() => {
  });
};

// 删除会话
const handleDelete = (session) => {
  ElMessageBox.confirm(`确定要删除会话「${session.name}」吗？`, '删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await deleteSession(session.id)
    const res = await sessionByUserId(user.value.id);
    sessions.value = res.data;
    if (currentSessionId.value === session.id) {
      currentSessionId.value = 0;
      messages.value = [];
    }
  }).catch(() => {
  });
};

// 删除消息
const handleDeleteMessage = (msg) => {
  ElMessageBox.confirm(`确定要删除该消息吗？`, '删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    const res = await deleteMessagesAfter(
        currentSessionId.value,
        msg.id
    )
    if (res.code) {
      ElMessage.success("删除成功");
      await handleSessionClick(currentSessionId.value);
    } else {
      ElMessage.error(res.msg);
    }
  }).catch(() => {
  });
};

// 创建会话
const createSessionBtn = async () => {
  const res = await createSession({
    user_id: user.value.id,
    name: "新建会话",
    create_time: null,
    update_time: null,
    id: null
  })

  if (res.code) {
    ElMessage.success("创建成功");
    const result = await sessionByUserId(user.value.id);
    sessions.value = result.data;
    currentSessionId.value = res.data.id;
    messages.value = []
  } else {
    ElMessage.error(res.msg);
  }
}

// 切换到我的页面
const switchToMyPage = async () => {
  if (user.value?.is_admin === 1) {
    await router.push({path: "/admin"})
  } else {
    await router.push({path: "/user"})
  }
}
</script>

<template>
  <div class="app-layout"> <!-- 替换 common-layout -->
    <header class="app-header">
      <div class="header-left">校灵通</div>
      <div class="header-center"></div>
      <div class="header-right">
        <a href="javascript:0" @click="switchToMyPage" class="my-btn">
          <el-icon><House /></el-icon> 我的
        </a>
        <a href="javascript:0" @click="logout" class="logout-btn">
          <el-icon><SwitchButton/></el-icon> 退出登录 【{{ user?.username }}】
        </a>
      </div>
    </header>

    <main class="app-main">
      <aside class="main-left">
        <div class="sessions-header">对话列表</div>
        <el-button type="primary" class="sessions-create-btn" @click="createSessionBtn">创建对话</el-button>
        <div class="sessions-list">
          <div
              v-for="session in sessions"
              :key="session.id"
              class="session-item"
              :class="{ 'is-active': session.id === currentSessionId }"
              @click="handleSessionClick(session.id)"
          >
            <div class="session-name">{{ session.name }}</div>
            <!-- 三个小点图标 + 弹出框 -->
            <el-popover
                placement="bottom-end"
                :width="120"
                trigger="click"
                popper-class="session-popover"
            >
              <template #reference>
                <span class="session-more-btn" @click.stop>⋯</span>
              </template>
              <div class="session-popover-menu">
                <div class="menu-item" @click.stop="handleRename(session)">重命名</div>
                <div class="menu-item danger" @click.stop="handleDelete(session)">删除</div>
              </div>
            </el-popover>
          </div>
          <div v-if="sessionsLoading" class="loading-text">加载中...</div>
          <div v-else-if="sessions && sessions.length === 0" class="empty-text">暂无会话</div>
        </div>
      </aside>

      <section class="main-chat">
        <!-- 上方：消息列表区域 -->
        <div class="chat-messages" ref="messagesContainer">
          <div v-for="(msg, index) in messages" :key="index" class="message-row"
               :class="msg.role === 'user' ? 'is-user' : 'is-assistant'">
            <span class="message-role">{{ msg.role === 'user' ? '我' : 'AI 助手' }}</span>
            <div class="message-bubble">
              <!-- 用户消息保持纯文本，AI消息使用 v-html 渲染 Markdown -->
              <template v-if="msg.role === 'user'">{{ msg.content }}</template>
              <div v-else class="markdown-body" v-html="md.render(msg.content)"></div>
            </div>
            <el-button class="message-delete-btn" size="small" type="danger" text @click="handleDeleteMessage(msg)">删除</el-button>
          </div>
        </div>

        <!-- 下方：输入区域 -->
        <div class="chat-input-area">
          <textarea
              v-model="inputContent"
              class="chat-textarea"
              placeholder="输入消息..."
              rows="1"
              @keydown.enter.exact.prevent="handleSend"
              @input="autoResizeTextarea"
              ref="textareaRef"
          ></textarea>
          <el-button type="primary" class="send-btn" @click="handleSend">发送</el-button>
        </div>
      </section>
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
  background-image: linear-gradient(to right, #00547d, #007fa4, #00aaa0);

}

.header-left {
    color: white;
    font-size: 40px;
    font-family: 楷体;
    line-height: 60px;
    font-weight: bolder;
}

.header-center {
  flex: 1;
  text-align: center;
}

.header-right {
  white-space: nowrap;
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

/* 当前选中的会话 - 蓝底 */
.session-item.is-active {
  background-color: #409eff;
}

.session-item.is-active .session-name {
  color: #fff;
}

.session-item.is-active .session-more-btn {
  color: #fff;
}

.session-item.is-active:hover {
  background-color: #409eff;
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
  display: flex;
  flex-direction: column;
  min-height: 0; /* 关键：允许内部 flex 子项收缩 */
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 0;
}

/* ===== 消息行容器：控制整体对齐 ===== */
.message-row {
  display: flex;
  flex-direction: column; /* 角色名在上，气泡在下 */
  margin-bottom: 16px;
}

/* Assistant 消息：靠左 */
.message-row.is-assistant {
  align-self: flex-start;
  align-items: flex-start;
}

/* User 消息：靠右 */
.message-row.is-user {
  align-self: flex-end;
  align-items: flex-end;
}

/* ===== 角色标签 ===== */
.message-role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
  padding: 0 4px;
}

/* ===== 消息气泡 ===== */
.message-bubble {
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  border-radius: 8px;
  position: relative;
}

/* 消息删除按钮 */
.message-delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
  align-self: flex-end;
}

.message-row.is-user .message-delete-btn {
  align-self: flex-end;
}

.message-row.is-assistant .message-delete-btn {
  align-self: flex-start;
}

.message-row:hover .message-delete-btn {
  opacity: 1;
}

/* Assistant 气泡样式 */
.is-assistant .message-bubble {
  background-color: #f0f2f5;
  color: #303133;
  border-top-left-radius: 2px; /* 左上角小圆角，模拟对话指向 */
}

/* User 气泡样式 */
.is-user .message-bubble {
  background-color: #409eff;
  color: #fff;
  border-top-right-radius: 2px; /* 右上角小圆角 */
}

.chat-input-area {
  flex-shrink: 0; /* 不被压缩 */
  display: flex;
  align-items: flex-end; /* 按钮对齐底部 */
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #dcdfe6;
  background-color: #fff;
}

.chat-textarea {
  flex: 1;
  resize: none; /* 禁止手动拖拽缩放 */
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  line-height: 24px; /* 与 JS 中 lineHeight 一致 */
  max-height: 120px; /* 5行 × 24px = 120px，CSS兜底 */
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
}

.chat-textarea:focus {
  border-color: #409eff;
}

.send-btn {
  flex-shrink: 0;
  height: 40px;
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

a {
  text-decoration: none;
}

.logout-btn {
  color: red;
  margin: 0 15px;
  font-size: 18px;
}

.my-btn {
  color: white;
  margin: 0 15px;
  font-size: 18px;
}

/* ===== 会话项改为 flex 布局 ===== */
.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* ===== 三个点按钮：默认隐藏，hover 时显示 ===== */
.session-more-btn {
  display: none; /* 默认隐藏 */
  font-size: 18px;
  color: #909399;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  flex-shrink: 0;
  user-select: none;
  border-radius: 4px;
  transition: background-color 0.2s, color 0.2s;
}

.session-more-btn:hover {
  color: #303133;
  background-color: #e4e7ed;
}

/* 鼠标移入 session-item 时显示三个点 */
.session-item:hover .session-more-btn {
  display: inline-block;
}

/* ===== 弹出框菜单样式 ===== */
.session-popover-menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-popover-menu .menu-item {
  padding: 8px 12px;
  font-size: 14px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
  color: #303133;
}

.session-popover-menu .menu-item:hover {
  background-color: #f5f7fa;
}

.session-popover-menu .menu-item.danger {
  color: #f56c6c;
}

.session-popover-menu .menu-item.danger:hover {
  background-color: #fef0f0;
}
</style>